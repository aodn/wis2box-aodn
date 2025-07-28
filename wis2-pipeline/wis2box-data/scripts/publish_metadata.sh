# Add data collection and publish the discovery metadata -- apollo-bay
docker exec -it wis2box-management bash -c '
  wis2box data add-collection /data/wis2box/metadata/discovery/apollo-bay.yml &&
  wis2box metadata discovery publish /data/wis2box/metadata/discovery/apollo-bay.yml
'
# Add data collection and publish the discovery metadata
docker exec -it wis2box-management bash -c '
  wis2box data add-collection /data/wis2box/metadata/discovery/storm-bay.yml &&
  wis2box metadata discovery publish /data/wis2box/metadata/discovery/storm-bay.yml
'
# Publish station metadata to a wmo topic
docker exec -it wis2box-management bash -c '
  wis2box metadata station publish-collection -p /data/wis2box/metadata/station/station_list.csv -th origin/a/wis2/au-bom-imos/data/core/ocean/surface-based-observations/wave-buoys
'

# OR manually update the metadata by login wis2box-management
# cd ~/wis2box
# # Login to the container (default: wis2box-management)
# python3 wis2box-ctl.py login
# wis2box data add-collection /data/wis2box/metadata/discovery/apollo-bay.yml &&
# wis2box metadata discovery publish /data/wis2box/metadata/discovery/apollo-bay.yml