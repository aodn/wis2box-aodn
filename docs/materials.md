This materials are copy from conference: **"WIS2 Community Workshop 2026"** used for AI to generate WORKSHOP CONTENT.

The goal of this workshop is to provide participants with a comprehensive understanding of the WMO WIS2 system and how to use it to publish and consume data. By the end of the workshop, participants should be able to:

- Understand the WMO WIS2 system and how it works
- Publish data to the WIS2 system
- Manage their own WIS2 node

1. Introduction
1.1 Introduction to WMO WIS2 system and core services on IMOS NODE
MQTT broker: 

Host: wis2box-broker.production.aodn.org.au

Port: 1883

Username: wis2box

Password: ask us if WMO need 

WIS2 Webapp: https://wis2.aodn.org.au/wis2box-webapp/

WIS2 pygeoapi: https://wis2.aodn.org.au/oapi/

Services on ECS production env:
1. wis2box-webapp: 
2. wis2box-management: 
3. wis2box-auth: 
4. wis2box-api: 
5. mosquitto: 
6. minio: 
7. elasticsearch: 

1.2 Metadata Management
The metadata consists of two components defined by WMO standards:

Station Metadata – Information describing the characteristics and details of observation stations.

Dataset Discovery Metadata – Information that enables users to find and understand datasets, including descriptions, keywords, and other discovery elements.



The station metadata on our node is:

Station name: Apollo-bay

WIGOS_ID: 0-22000-0-7811080

More Station metadata details can be see here: https://wis2.aodn.org.au/wis2box-webapp/station

The station metadata could be created as csv in WIS2BOX or retried from WIS2BOX Management service by WIGOS ID.

For the dataset discovery metadata, we manage it by WMO Standard YAML file to save it as Infrastructal As Code. Here is one sample of YAML file to manage the dataset of Aollo-Bay.

Meanwhile, we can also create or edit data discovery metadata on WIS2 Web application manually, like the dataset of Apollo-bay showed here. 

Currently, I am responsible for preparing metadata.

Metadata changes are infrequent. However, as we publish more datasets, a significant amount of new metadata will need to be created. Additionally, we require someone with deeper knowledge of metadata to edit and validate it.



There are two ways to publish datasets discovery metadata:

Publish metadata by wis2box-webapp manually.

Publish metadata by wis2box-management service with geo-YAML file.

 

1. Publish metadata by wis2box-webapp manually
Step1. Create an authorization token for processes/wis2box 
We need to create a token for the processes/wis2box endpoint firstly to edit metadata through wis2box-webapp.

Log in to the wis2box ec2 instance, then run the following commands. 



cd /home/ubuntu/wis2box
# Log in the wis2box-management service
python3 wis2box-ctl.py login
wis2box auth add-token --path processes/wis2box <copy process token from 1password>
Note: the process token can be found by search wis2box-management-processes in 1Password software as the following figure shown.

Screenshot from 2025-07-16 15-42-42.png
 

Step 2. Creating a new dataset in the wis2box-webapp
Fill in the information as the following figure's shown step by step.

Login wis2box-webapp, click Dataset Editor.

Screenshot from 2025-07-16 16-04-01-20250716-060401.png
A pop-up window will appear, asking we to provide:
Centre ID : this is the agency acronym (in locase and no spaces), as specified by the WMO Member, that identifies the data centre responsible for publishing the data.
Data Type: The type of data we are creating metadata for. We can choose between using a predefined template or selecting 'other'. If 'other' is selected, more fields will have to be manually filled.

Change Data Type into “others” instead of the default type.

Screenshot from 2025-06-16 16-00-40.png
 

Step 3. Creating discovery metadata
Edit Metadata

Screenshot from 2025-07-16 15-49-50-20250716-054950.png
Review the title and keywords, and update them as necessary, and provide a description for the dataset.
Note there are options to change the 'WMO Data Policy' from 'core' to 'recommended' or to modify default Metadata Identifier. We use 'core' here.
Next, review the section defining 'Temporal Properties' and 'Spatial Properties'. we can adjust the bounding box by updating the 'North Latitude', 'South Latitude', 'East Longitude', and 'West Longitude' fields (for example, Apollo Bay): (-38.75350, -38.75452, 143.72362, 143.72230)

Screenshot from 2025-06-16 16-22-35-20250616-062235.png
 

Next, fill out the section defining the 'Contact Information of the Data Provider':

Contact Information of the Data Provider

Organization Name: Integrated Marine Observing System (IMOS)

URL: Home - IMOS 

Email: imos@utas.edu.au

Phone: +61 (03) 6226 7549

Screenshot from 2025-07-07 14-08-22.png
Screenshot from 2025-07-15 13-46-47-20250715-034647.png
 

 

Configuring data mappings
Since we used a template to create dataset, the dataset mappings have been pre-populated with the defaults plugins for the 'weather/surface-based-observations/synop' data type. We need to change a wave_buoy_template which we created specific for IMOS Wave Buoy datasets. Data plugins are used in the wis2box to transform data before it is published using the WIS2 notification.

Note that we can click on the "update"-button to change settings for the plugin such as file-extension and the file-pattern, we can leave the default settings for now.  

Add the TOKEN for processing metadata, and then submit.

Screenshot from 2025-06-16 16-30-08.png
Check the message from MQTT broker that published by wis2box webapp for the dataset discovery metadata.

See the message from IMOS-WIS2 broker through MQTT Explorer:



{
  "id": "79fe8b11-6a90-456f-96b0-93fcb197fa51",
  "type": "Feature",
  "conformsTo": [
    "http://wis.wmo.int/spec/wnm/1/conf/core"
  ],
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [
          143.72362,
          -38.75452
        ],
        [
          143.7223,
          -38.75452
        ],
        [
          143.7223,
          -38.7535
        ],
        [
          143.72362,
          -38.7535
        ],
        [
          143.72362,
          -38.75452
        ]
      ]
    ]
  },
  "properties": {
    "data_id": "au-bom-imos/metadata/urn:wmo:md:au-bom-imos:poc-0uo5b",
    "datetime": "2025-06-17T00:21:27Z",
    "pubtime": "2025-06-17T00:21:28Z",
    "integrity": {
      "method": "sha512",
      "value": "QIETBgM4IaNiuX3g4Idc/TLr0aeqABQ/EHu/D94Hn+b7kDmk8osqHELJsuN+uGuw+Ir/J7zpK/RuuwfmijZNWQ=="
    },
    "content": {
      "encoding": "base64",
      "value": "eyJpZCI6ICJ1cm46d21vOm1kOmF1LWJvbS1pbW9zOnBvYy0wdW81YiIsICJjb25mb3Jtc1RvIjogWyJodHRwOi8vd2lzLndtby5pbnQvc3BlYy93Y21wLzIvY29uZi9jb3JlIl0sICJ0eXBlIjogIkZlYXR1cmUiLCAidGltZSI6IHsiaW50ZXJ2YWwiOiBbIjIwMjUtMDYtMTciLCAiLi4iXX0sICJnZW9tZXRyeSI6IHsidHlwZSI6ICJQb2x5Z29uIiwgImNvb3JkaW5hdGVzIjogW1tbMTQzLjcyMzYyLCAtMzguNzU0NTJdLCBbMTQzLjcyMjMsIC0zOC43NTQ1Ml0sIFsxNDMuNzIyMywgLTM4Ljc1MzVdLCBbMTQzLjcyMzYyLCAtMzguNzUzNV0sIFsxNDMuNzIzNjIsIC0zOC43NTQ1Ml1dXX0sICJwcm9wZXJ0aWVzIjogeyJ0eXBlIjogImRhdGFzZXQiLCAiaWRlbnRpZmllciI6ICJ1cm46d21vOm1kOmF1LWJvbS1pbW9zOnBvYy0wdW81YiIsICJ0aXRsZSI6ICJEcmlmdGluZyBidW95IG9ic2VydmF0aW9ucyBtYWRlIGFzIHBhcnQgb2YgdGhlIC0tQm91eS0tIHByb2dyYW0iLCAiZGVzY3JpcHRpb24iOiAicG9jIHRlc3QgcHVibGlzaCBtZXRhZGF0YSBvZiBib3V5IGRhdGFzZXQiLCAia2V5d29yZHMiOiBbIm9jZWFucyIsICJzdXJmYWNlIGN1cnJlbnQiLCAic2VhIHN1cmZhY2UgdGVtcGVyYXR1cmUiLCAic2VhIGxldmVsIHByZXNzdXJlIiwgImxhZ3JhbmdpYW4gZHJpZnRlciIsICJnb29zIl0sICJ0aGVtZXMiOiBbeyJjb25jZXB0cyI6IFt7ImlkIjogImNsaW1hdGUiLCAidGl0bGUiOiAiQ2xpbWF0ZSJ9LCB7ImlkIjogIm9jZWFuIiwgInRpdGxlIjogIk9jZWFuIn0sIHsiaWQiOiAid2VhdGhlciIsICJ0aXRsZSI6ICJXZWF0aGVyIn1dLCAic2NoZW1lIjogImh0dHA6Ly9jb2Rlcy53bW8uaW50L3dpcy90b3BpYy1oaWVyYXJjaHkvZWFydGgtc3lzdGVtLWRpc2NpcGxpbmUifV0sICJjb250YWN0cyI6IFt7Im9yZ2FuaXphdGlvbiI6ICJJbnRlZ3JhdGVkIE1hcmluZSBPYnNlcnZpbmcgU3lzdGVtIChJTU9TKSIsICJlbWFpbHMiOiBbeyJ2YWx1ZSI6ICJpbW9zQHV0YXMuZWR1LmF1In1dLCAiYWRkcmVzc2VzIjogW3siY291bnRyeSI6ICJBVVMifV0sICJsaW5rcyI6IFt7InJlbCI6ICJhYm91dCIsICJocmVmIjogImh0dHBzOi8vaW1vcy5vcmcuYXUvIiwgInR5cGUiOiAidGV4dC9odG1sIn1dLCAicm9sZXMiOiBbImhvc3QiXSwgInBob25lcyI6IFt7InZhbHVlIjogIis2MTM2MjI2NzU0OSJ9XX1dLCAiY3JlYXRlZCI6ICIyMDI1LTA2LTE3VDAwOjIxOjI3WiIsICJ1cGRhdGVkIjogIjIwMjUtMDYtMTdUMDA6MjE6MjdaIiwgIndtbzpkYXRhUG9saWN5IjogInJlY29tbWVuZGVkIiwgImlkIjogInVybjp3bW86bWQ6YXUtYm9tLWltb3M6cG9jLTB1bzViIn0sICJsaW5rcyI6IFt7ImhyZWYiOiAibXF0dDovL2V2ZXJ5b25lOmV2ZXJ5b25lQGltb3Mtd2lzLmRldi5hb2RuLm9yZy5hdToxODgzIiwgInR5cGUiOiAiYXBwbGljYXRpb24vanNvbiIsICJuYW1lIjogIm9yaWdpbi9hL3dpczIvYXUtYm9tLWltb3MvZGF0YS9yZWNvbW1lbmRlZC9vY2Vhbi9zdXJmYWNlLWJhc2VkLW9ic2VydmF0aW9ucy9kcmlmdGluZy1idW95cyIsICJyZWwiOiAiaXRlbXMiLCAiY2hhbm5lbCI6ICJvcmlnaW4vYS93aXMyL2F1LWJvbS1pbW9zL2RhdGEvcmVjb21tZW5kZWQvb2NlYW4vc3VyZmFjZS1iYXNlZC1vYnNlcnZhdGlvbnMvZHJpZnRpbmctYnVveXMiLCAidGl0bGUiOiAiTm90aWZpY2F0aW9ucyJ9XX0=",
      "size": 1691
    }
  },
  "links": [
    {
      "rel": "canonical",
      "type": "application/geo+json",
      "href": "http://imos-wis.dev.aodn.org.au/data/metadata/urn:wmo:md:au-bom-imos:poc-0uo5b.json",
      "length": 1691
    }
  ],
  "generated_by": "wis2box 1.0.0"
}
origin/a/wis2/au-bom-imos/metadata
The above mqtt message may outdated, but structure would be similar.

Copy the href link into the browser, and we will see all metadata to discover the Bouy dataset.



{
  "id": "urn:wmo:md:au-bom-imos:poc-0uo5b",
  "conformsTo": [
    "http://wis.wmo.int/spec/wcmp/2/conf/core"
  ],
  "type": "Feature",
  "time": {
    "interval": [
      "2025-06-17",
      ".."
    ]
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [143.72362, -38.75452],
        [143.7223, -38.75452],
        [143.7223, -38.7535],
        [143.72362, -38.7535],
        [143.72362, -38.75452]
      ]
    ]
  },
  "properties": {
    "type": "dataset",
    "identifier": "urn:wmo:md:au-bom-imos:poc-0uo5b",
    "title": "Drifting buoy observations made as part of the --Bouy-- program",
    "description": "poc test publish metadata of bouy dataset",
    "keywords": [
      "oceans",
      "surface current",
      "sea surface temperature",
      "sea level pressure",
      "lagrangian drifter",
      "goos"
    ],
    "themes": [
      {
        "concepts": [
          {
            "id": "climate",
            "title": "Climate"
          },
          {
            "id": "ocean",
            "title": "Ocean"
          },
          {
            "id": "weather",
            "title": "Weather"
          }
        ],
        "scheme": "http://codes.wmo.int/wis/topic-hierarchy/earth-system-discipline"
      }
    ],
    "contacts": [
      {
        "organization": "Integrated Marine Observing System (IMOS)",
        "emails": [
          {
            "value": "imos@utas.edu.au"
          }
        ],
        "addresses": [
          {
            "country": "AUS"
          }
        ],
        "links": [
          {
            "rel": "about",
            "href": "https://imos.org.au/",
            "type": "text/html"
          }
        ],
        "roles": [
          "host"
        ],
        "phones": [
          {
            "value": "+61362267549"
          }
        ]
      }
    ],
    "created": "2025-06-17T00:21:27Z",
    "updated": "2025-06-17T00:21:27Z",
    "wmo:dataPolicy": "recommended",
    "id": "urn:wmo:md:au-bom-imos:poc-0uo5b"
  },
  "links": [
    {
      "href": "mqtt://everyone:everyone@imos-wis.dev.aodn.org.au:1883",
      "type": "application/json",
      "name": "origin/a/wis2/au-bom-imos/data/recommended/ocean/surface-based-observations/drifting-buoys",
      "rel": "items",
      "channel": "origin/a/wis2/au-bom-imos/data/recommended/ocean/surface-based-observations/drifting-buoys",
      "title": "Notifications"
    }
  ]
}
 

2. Publish metadata by wis2box-management service by geo-YAML file.
This method keeps the discovery metadata in a persistent way
create discovery metadata yml file in MCF geo-metadata format.



wis2box:
    retention: P30D
    topic_hierarchy: au-imos/data/core/ocean/surface-based-observations/wave-buoys
    country: AUS
    centre_id: au-imos
    data_mappings:
        plugins:
            csv:
                - plugin: wis2box.data.csv2bufr.ObservationDataCSV2BUFR
                  template: wave_buoy_template
                  notify: true
                  buckets:
                    - ${WIS2BOX_STORAGE_INCOMING}
                  file-pattern: '.*\.csv$'
            bufr4:
                - plugin: wis2box.data.bufr2geojson.ObservationDataBUFR2GeoJSON
                  buckets:
                    - ${WIS2BOX_STORAGE_INCOMING}
                  file-pattern: '.*\.bufr4$'
mcf:
    version: 1.0
metadata:
    identifier: urn:wmo:md:au-imos:wave-buoys
    hierarchylevel: dataset
identification:
    title: Wave buoy observations made as part of the -- IMOS-WIS2.0
    abstract: Australian IMOS-WIS2.0 coastal wave buoy observations
    dates:
        creation: 2025-07-30
    keywords:
        default:
            keywords:
                - surface weather
                - observations
                - ocean
                - surface current
        wmo:
            keywords:
                - ocean
            keywords_type: theme
            vocabulary:
                name: Earth system disciplines as defined by the WMO Unified Data Policy, Resolution 1 (Cg-Ext(2021), Annex 1.
                url: https://codes.wmo.int/wis/topic-hierarchy/earth-system-discipline
    extents:
        spatial:
            - bbox: [112.00000,-44.00000,155.00000,-10.00000]
              crs: 4326
        temporal:
            - begin: 2025-08-30 # Set the date once productionized
              end: null
              resolution: PT30M # temporal resolution of the data, meaning how frequently observations are collected or reported.
                                # Every 30 minutes
    url: https://thredds.aodn.org.au/thredds/catalog/IMOS/COASTAL-WAVE-BUOYS/WAVE-BUOYS/REALTIME/WAVE-PARAMETERS/catalog.html
    wmo_data_policy: core
contact:
    host:
        organization: Integrated Marine Observing System (IMOS)
        url: https://imos.org.au/
        individualname: Integrated Marine Observing System (IMOS)
        positionname: Integrated Marine Observing System (IMOS)
        phone: "+61362267549"
        fax: null
        address: GPO Box 367, Hobart
        city: Hobart
        postalcode: "7001"
        administrativearea: Hobart
        country: Australia
        email: imos@utas.edu.au
        hoursofservice: 2200h - 0600h UTC
        contactinstructions: email
login the wis2box-management service

add the dataset collection

publish dataset discovery  metadata 

CLI



cd ~/wis2box
python3 wis2box-ctl.py login
wis2box data add-collection <path to discovery-meatadata path>
# eg:
# wis2box data add-collection /data/wis2box/metadata/discovery/apollo-bay.yml 
wis2box metadata discovery publish <path to discovery-meatadata path>
# eg:
# wis2box metadata discovery publish /data/wis2box/metadata/discovery/apollo-bay.yml
other commands to managing discovery metadata:



Usage: wis2box metadata discovery [OPTIONS] COMMAND [ARGS]...
  Discovery metadata management
Options:
  --help  Show this message and exit.
Commands:
  publish    Inserts or updates discovery metadata to catalogue
  republish  Republish all published discovery metadata
  setup      Initializes metadata repository
  unpublish  Deletes a discovery metadata record from the catalogue


Usage: wis2box data [OPTIONS] COMMAND [ARGS]...
  Data workflow
Options:
  --help  Show this message and exit.
Commands:
  add-collection            Add collection index to API backend
  add-collection-items      Add collection items to API backend
  clean                     Clean data from storage older than X days
  delete-collection         Delete collection from API backend
  ingest                    Ingest data file or directory
  reindex-collection-items  Reindex items from one collection to another



  Source Netcdf
IMOS/COASTAL-WAVE-BUOYS/WAVE-BUOYS/REALTIME/WAVE-PARAMETERS/APOLLO-BAY

Varaiable attributes: 



{
    "ancillary_variable": "WAVE_quality_control",
    "comment": "Direction (related to the magnetic north) from which the mean period waves are coming from",
    "compass_correction_applied": 13,
    "long_name": "spectral sea surface wave mean direction",
    "magnetic_declination": 12.86,
    "method": "Spectral analysis method",
    "positive": "clockwise",
    "reference_datum": "true north",
    "standard_name": "sea_surface_wave_from_direction",
    "units": "Degrees",
    "valid_max": 360.0,
    "valid_min": 0.0,
    "name": "SSWMD"
},
{
    "flag_meanings": "good not_evaluated questionable bad missing",
    "flag_values": [
        1,
        2,
        3,
        4,
        9
    ],
    "long_name": "primary Quality Control flag for wave variables",
    "quality_control_convention": "Ocean Data Standards, UNESCO 2013 - IOC Manuals and Guides, 54, Volume 3 Version 1",
    "valid_max": 9,
    "valid_min": 1,
    "name": "WAVE_quality_control"
},
{
    "ancillary_variable": "WAVE_quality_control",
    "long_name": "spectral sea surface wave mean directional spread",
    "method": "Spectral analysis method",
    "positive": "clockwise",
    "standard_name": "sea_surface_wave_directional_spread",
    "units": "Degrees",
    "valid_max": 360.0,
    "valid_min": 0.0,
    "name": "WMDS"
},
{
    "ancillary_variable": "WAVE_quality_control",
    "comment": "Direction (related to the magnetic north) from which the peak period waves are coming from",
    "compass_correction_applied": 13,
    "long_name": "spectral peak wave direction",
    "magnetic_declination": 12.86,
    "method": "Spectral analysis method",
    "positive": "clockwise",
    "reference_datum": "true north",
    "standard_name": "sea_surface_wave_from_direction_at_variance_spectral_density_maximum",
    "units": "Degrees",
    "valid_max": 360.0,
    "valid_min": 0.0,
    "name": "WPDI"
},
{
    "ancillary_variable": "WAVE_quality_control",
    "long_name": "spectral sea surface wave peak directional spread",
    "method": "Spectral analysis method",
    "positive": "clockwise",
    "reference_datum": "true north",
    "standard_name": "sea_surface_wave_directional_spread_at_variance_spectral_density_maximum",
    "units": "Degrees",
    "valid_max": 360.0,
    "valid_min": 0.0,
    "name": "WPDS"
},
{
    "ancillary_variable": "WAVE_quality_control",
    "long_name": "sea surface wave spectral mean period",
    "method": "Spectral analysis method",
    "standard_name": "sea_surface_wave_mean_period_from_variance_spectral_density_first_frequency_moment",
    "units": "s",
    "valid_max": 50.0,
    "valid_min": 0.0,
    "name": "WPFM"
},
{
    "ancillary_variable": "WAVE_quality_control",
    "comment": "Period of the peak of the energy spectrum",
    "long_name": "peak wave spectral period",
    "method": "Spectral analysis method",
    "standard_name": "sea_surface_wave_period_at_variance_spectral_density_maximum",
    "units": "s",
    "valid_max": 50.0,
    "valid_min": 0.0,
    "name": "WPPE"
},
{
    "ancillary_variable": "WAVE_quality_control",
    "long_name": "sea surface wave spectral significant height",
    "method": "Spectral analysis method",
    "standard_name": "sea_surface_wave_significant_height",
    "units": "m",
    "valid_max": 100.0,
    "valid_min": 0.0,
    "name": "WSSH"
},
 

Bufr Template for WAVE BOUY: 
Template Examples

Moored buoy template 315008: https://wmoomm.sharepoint.com/:w:/s/wmocpdb/EV-Qy69yaThAm6ZlO47JpDoBHupCplErRMHK4ftu62BCMA?e=CbqRO9Connect your OneDrive account 

Wave buoy template 308015:https://wmoomm.sharepoint.com/:w:/s/wmocpdb/EUQsB14SxBNGod45ie-Ae9cBsftDsn36RzjYVG-3_6XqMg?e=v49YOAConnect your OneDrive account 

 

Wave Buoy Mapping Table:
This table is used to convert the Netcdf into BUFR format by mapping the IMOS data variables into WMO Elements. 

NetCDF name → Element Name (from wave buoy template) → Table Reference code ID → Element Key → BUFR eccodes_key

NetCDF Variable Name

NetCDF Variable

Standard Name

NetCDF Variable Long Name

WMO Table Reference

Element Name

Element Key

Eccodes_key

Comments

SSWMD

sea_surface_wave_from_direction

spectral sea surface wave mean direction

022086

MEAN DIRECTION FROM WHICH WAVES ARE COMING

meanDirectionFromWhichWavesAreComing

#1#meanDirectionFromWhichWavesAreComing

 

WAVE_quality_control

 

 

 

 

 

 

 

WMDS

sea_surface_wave_directional_spread

spectral sea surface wave mean directional spread


what is spectral sea surface wave mean directional spread?.docx
17 Jul 2025, 09:32 AM
 

022187

DIRECTIONAL SPREAD OF WAVE

directionalSpreadOfWaves

#1#directionalSpreadOfWaves

Is this express the directional spread of “any wave as 002187, as opposed to the directional spread of “dominant wave” (0 22 077)?

WPDI

sea_surface_wave_from_direction_at_variance_spectral_density_maximum

spectral peak wave direction

022076

DIRECTION FROM WHICH DOMINANT WAVES ARE COMING

directionFromWhichDominantWavesAreComing

#1#directionFromWhichDominantWavesAreComing

Is the peak wave equals to Dominant Wave?

Cannot find the peak wave direction in element tables. 

Assume the peak wave equals to the Dominant Wave. Need double-check from professionals.

WPDS

sea_surface_wave_directional_spread_at_variance_spectral_density_maximum

spectral sea surface wave peak directional spread

 

022077

 

DIRECTIONAL SPREAD OF DOMINANT WAVE

directionalSpreadOfDominantWave

#1#directionalSpreadOfDominantWave

 

WPFM

sea_surface_wave_mean_period_from_variance_spectral_density_first_frequency_moment

sea surface wave spectral mean period

 

022074

Average wave period 

averageWavePeriod

#1#averageWavePeriod

The Perplexity Answer the “Average wave period is not equal to sea surface wave spectral mean period”. more details here: what is sea surface wave spectral mean period_ is.docx

However, the WMO reference table dose not include sea surface wave spectral mean period, only has Average wave period. Not sure what is the meaning of this variable.

Assume they are equal. We can rename later if not correct.

 

WPPE

sea_surface_wave_period_at_variance_spectral_density_maximum

peak wave spectral period

022071

Spectral peak wave period

spectralPeakWavePeriod

#1#spectralPeakWavePeriod

 

WSSH

sea_surface_wave_significant_height

sea surface wave spectral significant height

022070

Significant wave height

 significantWaveHeight

#1#significantWaveHeight

 

 

Resources:

BOM wave observations Located at 42.20S, 145.05E
(Approximately 10 km West of Cape Sorell, West Tasmania)

HOW BOM provides forecasts of wave heights

what is WAVE BUOY and how it works.

BUOYs Types: drifting buoys, moored buoys, wave bouys, ice bouys and so on.

VIDEOS

Understanding Waves

How do wave buoys measure waves around our coastline?

Screenshot from 2025-07-03 16-05-11.png
 


 Require WIGOS-ID:
WIGOS Station Identifier (WSI) for IMOS WAVE BOUY data

Check the WIGOS ID on:

 OceanOPS

OSCAR eg. one of WISGO ID Global Atmosphere Watch Station Information System (GAWSIS)

!! WIS2 cannot publish data without WIGOS ID. DO CONFIRM that WIGOS ID is accessible on OSCAR.!!

 

Publishing weather station metadata
There are two ways to publish datasets discovery metadata:

Publish weather station metadata by wis2box-webapp manually.

Publish weather station metadata by wis2box-management service with csv file.

 

1. Publish weather station metadata by wis2box-webapp manually.
Create an authorization token for collections/stations


## when using efs:
## cd /mnt/efs-mount-point/wis2box
## Otherwise:
cd /home/ubuntu/wis2box
python3 wis2box-ctl.py login
wis2box auth add-token --path collections/stations <copy process token from 1password>
 

Wait for WIGOS ID from BOM. For testing IMOS WIS2 SYSTEM, we can use 0-20000-0-91334, which is a wmo testing ID, to create weather station metadata and see the publications.

 step 1. Put your WIGOS ID on WIS2box-webapp 
Screenshot from 2025-08-04 11-11-33-20250804-011133.png
Screenshot from 2025-08-04 11-10-16-20250804-011016.png
Step 2. Click on SEARCH
Now you can see your weather station that imported from OSCAR if the WIGOS ID is registered on OSCAR.

Screenshot from 2025-08-04 11-22-41-20250804-012241.png
Details of the weather station including WIGOS ID, station name, geometry etc.
step 3. Confirm the weather station info
Confirm with the facility type, Barometer height above seal level, WMO Region and so on. 

acf91e32-573c-49ed-8cca-0c123f6e63ba.png
step 4. Select corresponding topics for the station
The topic is an WMO hierarchical topic used as MQTT Message sub/pub TOPIC.

Screenshot from 2025-08-04 11-31-07-20250804-013107.png
step 5. Put your authorization token inside the collections/stations box
 

Screenshot from 2025-08-04 11-34-38-20250804-013438.png
step 6. Click save and publish
Screenshot from 2025-08-04 11-36-51-20250804-013651.png
now your station metadata is published on WIS2 Node. 

Screenshot from 2025-08-04 11-39-39-20250804-013939.png
 

2. Publish weather station metadata by wis2box-management service with csv file.
Step 1. Prepare weather station csv file
The CSV must have exactly the same column names as 

station_name,wigos_station_identifier,traditional_station_identifier,facility_type,latitude,longitude,elevation,barometer_height,territory_name,wmo_region

For example, a standard csv here:


station_list.csv
04 Aug 2025, 11:48 AM
Step 2. Publish weather station meatadata by code
Login to the wis2box-management service



# 1. Navigate to your wis2box directory:
cd ~/wis2box
#
# 2. Login to the management container:
python3 wis2box-ctl.py login
# 3. Publish weather station meatadata
wis2box metadata station publish-collection \
    -p /data/wis2box/metadata/station/station_list.csv \
    -th origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
or run publish_metadata.sh directly.

 

 

 

Other Helpful Tips: 
1. Volume mappings between the efs and the wis2box instance:


MINIO:
      volumes:
      - /mnt/efs-mount-point/minio-data:/data
      ## Move the minIO volume to EFS as persistent volume
      - ${WIS2BOX_HOST_DATADIR}/.ssh:/home/miniouser/.ssh:ro
# directory on the host with wis2box-configuration
WIS2BOX_HOST_DATADIR=/mnt/efs-mount-point/wis2box-data
# directory in the wis2box container with wis2box-configuration
WIS2BOX_DATADIR=/data/wis2box
All data saved in /mnt/efs-mount-point/wis2box-data will be used wis2box services. eg.wis2box-management (python3 wis2box-ctl.py login)

This folder saved metadata for the wis2 system:

/mnt/efs-mount-point/wis2box-data/mappings : stored the csv2burf plug-in mapping templates, eg. wave_buoy_template.json

/mnt/efs-mount-point/wis2box-data/metadata/discovery : stored the wis2box discovery metadata files eg. apollo-bay.yml

/mnt/efs-mount-point/wis2box-data/metadata/station: stored the wis2box station metadata as station_list.csv

 

The data in /mnt/efs-mount-point/minio-data/  are used by MINIO.

mapping /mnt/efs-mount-point/minio-data/wis2box-incoming with MINIO wis2box-incoming bucket

mapping /mnt/efs-mount-point/minio-data/wis2box-public with MINIO wis2box-public bucket

 

 

2. Sync efs wis data into the local machine:
ssh ec2

copy files from efs to ec2 instance



ubuntu@ip-10-1-1-48:/mnt/efs-mount-point$ sudo cp -r /mnt/efs-mount-point/ /home/ubuntu/efs/
open your local machine terminal and SCP efs folder into local machine



scp -i wis2.pem -r ubuntu@16.176.5.167:/home/ubuntu/efs/ /home/xiaohul/efs
Other useful Commands


Usage: wis2box metadata station [OPTIONS] COMMAND [ARGS]...
  Station metadata management
Options:
  --help  Show this message and exit.
Commands:
  add-topic           Adds topic to station metadata
  get                 Queries OSCAR/Surface for station information
  publish-collection  Publish from station_list.csv
  setup               Initializes metadata repository


Usage: wis2box metadata [OPTIONS] COMMAND [ARGS]...
  Metadata management
Options:
  --help  Show this message and exit.
Commands:
  discovery  Discovery metadata management
  station    Station metadata management


Usage: wis2box data [OPTIONS] COMMAND [ARGS]...
  Data workflow
Options:
  --help  Show this message and exit.
Commands:
  add-collection            Add collection index to API backend
  add-collection-items      Add collection items to API backend
  clean                     Clean data from storage older than X days
  delete-collection         Delete collection from API backend
  ingest                    Ingest data file or directory
  reindex-collection-items  Reindex items from one collection to another


  MINIO 
Install MINIO client edge account: AIStor Client 



mc alias set myminio https://minioserver.example.net ACCESS_KEY SECRET_KEY
# set on you local machine to connect the remote MINIO
mc alias set wis2box-edge https://wis2box.edge.aodn.org.au ACCESS_KEY(get-it-from-aws-Parameter-Store) SECRET_KEY(get-it-from-aws-Parameter-Store)
LS Objects:



mc ls wis2-aodn/wis2box-public/
CP local testing file into MINIO:



mc cp /home/leoli/Downloads/WIGOS_0-22000-0-7811080_20260123T012500.csv wis2-aodn/wis2box-incoming/urn:wmo:md:au-imos:wave-buoys/WIGOS_0-22000-0-7811080_20260123T012500.csv
delete objects



mc rm -r --force wis2-aodn/wis2box-public/2025-08-27/
 

MINIO-GUI: 

rclone is a very useful GUI tool for minio. 

Screenshot from 2025-09-17 12-57-32.png


# donwload and install rclone:
sudo -v ; curl https://rclone.org/install.sh | sudo bash
# Config connection with remote storage provider
rclone config
# Display the GUI of minio
rclone rcd --rc-web-gui
 

 

Login wis2box-management services
If you didn’t install the aws session-manager-plugin, install them on your terminal:



curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
then login aws edge account:



export AWS_PROFILE=edge-admin
aws sso login
login ecs by execute-command:



aws ecs execute-command \
  --region ap-southeast-2 \
  --cluster wis2box-edge \
  --task 65242b46f3624091915c1ffe55a8aaf7 \
  --container wis2box-management \
  --command "sh" \
  --interactive
Check wis2box CLI on ecs wis2box-management service: wis2box

Publishing discovery metadata after logged in:
1.Manually publish:



wis2box data add-collection /data/wis2box/metadata/discovery/wave-buoys.yml
wis2box metadata discovery publish /data/wis2box/metadata/discovery/wave-buoys.yml
add topic if the topic is not published:



wis2box metadata station add-topic origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
 

2.Script to publish



cd /data/wis2box/scripts/
bash publish_metadata.sh
 

Publish station metadata:


wis2box metadata station publish-collection \
    -p /data/wis2box/metadata/station/station_list.csv \
    -th origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
Unpublishing discovery metadata after logged in:


cd /data/wis2box/scripts/
bash unpublish_metadata.sh
 

Manually unpublish discovery metadata one by one:



#  Inside the container, run the unpublish commands individually:
wis2box metadata discovery unpublish urn:wmo:md:au-imos:wave-buoys
wis2box data delete-collection urn:wmo:md:au-imos:wave-buoys
 

Manage datasets publication:

cd /data/wis2box/ to the wis2box metadata management folder



# run the commands individually:
wis2box data add-collection /data/wis2box/metadata/discovery/wave-buoys.yml
wis2box metadata discovery publish /data/wis2box/metadata/discovery/wave-buoys.yml
 

Add Token on Management Service: 



wis2box auth add-token --path processes/wis2box
wis2box auth add-token --path collections/stations
 

 

WIS2 data pipeline:

csv push to minio wis2 incoming bucket, dataset identifier folder

dataset identifier folder is a foler name used dataset identifier as folder name

Screenshot from 2025-09-11 13-15-06.png
minio object put event triggerred pipeline converting and publishing BUFR to public bucket

send MQTT message to WIS2.0 node according the minio event on dataset identifier folder

 

 

Manually prepare wis2box metadata system dependencies for the ecs provision:


# prepare metadata files for publish wis2 metadata
cd /data/wis2box
rm -rf mappings
rm -rf metadata
git clone https://github.com/aodn/wis2box-aodn.git
mv wis2box-aodn/wis2-pipeline/wis2box-data/metadata metadata
mv wis2box-aodn/wis2-pipeline/wis2box-data/mappings mappings
mv wis2box-aodn/wis2-pipeline/wis2box-data/scripts scripts
rm -rf wis2box-aodn
# run the command below to add topic for wave buoys
wis2box metadata station add-topic origin/a/wis2/au-imos/data/core/ocean/surface-based-observations/wave-buoys
 

 

Files successfully published to WIS2 node:

Screenshot from 2025-11-10 16-52-14.png
MQTT message on AU-BOM-IMOS WIS2 Node
MQTT message in JSON (get from WIS2 node):



{
   "id":"8fe2e9a1-f5c0-4aee-ba81-1557171b64bd",
   "type":"Feature",
   "conformsTo":[
      "http://wis.wmo.int/spec/wnm/1/conf/core"
   ],
   "geometry":{
      "coordinates":[
         143.72295,
         -38.75467
      ],
      "type":"Point"
   },
   "properties":{
      "data_id":"au-bom-imos:wave-buoys/WIGOS_0-22000-0-7811080_20251109T222000",
      "datetime":"2025-11-09T22:20:00Z",
      "pubtime":"2025-11-10T05:45:28Z",
      "integrity":{
         "method":"sha512",
         "value":"ingrYcRoib4lCuLvWZc6sd9ialH+Ncn+LdD26/1cI6+xjyAujYTgz0n3BmRjTSJ4RJX5wuri2zBGYOQmuWDp5w=="
      },
      "metadata_id":"urn:wmo:md:au-bom-imos:wave-buoys",
      "content":{
         "encoding":"base64",
         "value":"QlVGUgAAegQAABYAAGL//wAAAAZuKQAH6QsJFhQAAAAJAAABgMgPAABPACIrSP/////////////////v02TZQnGNq9vsj//7DCv/////+CrM3/8j////////gP//////wH//7I///+A//////8NgP///////4Dc3Nzc=",
         "size":122
      },
      "wigos_station_identifier":"0-22000-0-7811080"
   },
   "links":[
      {
         "rel":"canonical",
         "type":"application/bufr",
         "href":"https://wis2box.edge.aodn.org.au/data/2025-11-09/wis/urn:wmo:md:au-bom-imos:wave-buoys/WIGOS_0-22000-0-7811080_20251109T222000.bufr4",
         "length":122
      },
      {
         "rel":"via",
         "type":"text/html",
         "href":"https://oscar.wmo.int/surface/#/search/station/stationReportDetails/0-22000-0-7811080"
      }
   ],
   "generated_by":"wis2box 1.0.0"
}