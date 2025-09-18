# !/bin/bash
## This script used for updating the wis2box metadata files in the wis2box-management ecs container
git clone https://github.com/aodn/wis2box-aodn.git

## sync the updated metadata files to the /data.wis2box-data folder
rsync -a ./wis2box-aodn/wis2-pipeline/wis2box-data/ ./wis2-pipeline/wis2box-data/
rm -rf wis2box-aodn
