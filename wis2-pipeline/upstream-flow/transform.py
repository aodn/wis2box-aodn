from pydantic import BaseModel, computed_field
from typing import ClassVar
from prefect import get_run_logger, task
import pandas as pd
import xarray as xr
from tempfile import mkdtemp, gettempdir

class Buoy(BaseModel):
    """A class to represent a buoy and convert its NetCDF data to CSV format.

    Attributes
    ----------
    wigos_id : str
        The WMO WIGOS ID of the buoy.
    nc_file_path : str
        The path of the NetCDF file containing buoy data.
    csv_path : str
        The path for the output CSV file based on the WIGOS ID and timestamp.
    Methods
    -------
    get_netcdf(nc_file_path: str) -> xr.Dataset:
        Retrieves the NetCDF data from the specified path.
    nc_to_csv() -> None:
        Converts the NetCDF file to a CSV file with appropriate headers and metadata.
        And saves it to the constructed CSV path.

    Raises
    ------
    ValueError
        If the WIGOS ID is not provided.

    Notes
    -----
    The WIGOS ID is used to identify the buoy and construct the output CSV file name.
    The NetCDF file is expected to contain a TIME variable for time stamping the data.
    The CSV file will include additional metadata such as region number, block number,
        and station number derived from the WIGOS ID.
    """

    wigos_id: str
    nc_file_path: str
    temp_dir: str = mkdtemp(prefix="buoy_temp_", dir=gettempdir())
    nc_to_csv: ClassVar[callable]

    def __repr__(self):
        return f"Buoy(wigos_id={self.wigos_id})"

    @computed_field
    @property
    def csv_path(self) -> str:

        ds = self.get_netcdf(self.nc_file_path)
        # Extract the time from the dataset
        data_time = ds.TIME.values
        # Convert numpy datetime64 to pandas datetime and format as string
        data_time_str = pd.to_datetime(data_time).strftime('%Y%m%dT%H%M%S')

        return f"{self.temp_dir}/WIGOS_{self.wigos_id}_{data_time_str}.csv"

    def get_netcdf(self, nc_file_path:str) -> xr.Dataset:
        """Retrieve the NetCDF data from the specified path."""
        ds = xr.open_dataset(nc_file_path, engine="netcdf4")
        # only keep the last time step
        ds = ds.isel(TIME=-1)
        return ds

    @task()
    def nc_to_csv(self) -> None:
        """Convert a NetCDF file of buoy data to a CSV file.
        The CSV file will include WIGOS metadata and time information.
        """
        ds = self.get_netcdf(self.nc_file_path)

        logger = get_run_logger()
        logger.info(f"Processing NetCDF file: {self.nc_file_path}")

        df =  ds.to_dataframe()
        df.reset_index(inplace=True)

        # Prepare the WMO BUFR header information
        wigos_id = self.wigos_id
        if not wigos_id:
            raise ValueError("WIGOS ID is required to process the buoy data.")

        # Prepare the WIGOS metadata and save to dataframe
        buoyOrPlatformIdentifier = wigos_id[-5:]
        df['regionNumber'] = buoyOrPlatformIdentifier[0]
        df['wmoRegionSubArea'] = buoyOrPlatformIdentifier[1]
        df['buoyOrPlatformIdentifier'] = buoyOrPlatformIdentifier
        df['blockNumber'] = buoyOrPlatformIdentifier[0:2]
        df['stationNumber'] = buoyOrPlatformIdentifier[2:5]
        df['wigos_station_identifier'] = wigos_id
        df['year'] = df['TIME'].dt.year
        df['month'] = df['TIME'].dt.month
        df['day'] = df['TIME'].dt.day
        df['hour'] = df['TIME'].dt.hour
        df['minute'] = df['TIME'].dt.minute
        df['second'] = df['TIME'].dt.second
        df.rename(columns={'LATITUDE': 'latitude',
                        'LONGITUDE': 'longitude'
                        }, inplace=True)

        output_file_path = self.csv_path

        logger.info(f"Saving DataFrame to CSV file: {output_file_path}")
        df.to_csv(output_file_path, index=False)
