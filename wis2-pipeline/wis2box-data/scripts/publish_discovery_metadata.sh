cd ~/wis2box
# login to the container (default: wis2box-management)
python3 wis2box-ctl.py login
# add data collection and publish the discovery metadata
docker exec -it wis2box-management bash -c '
  wis2box data add-collection /data/wis2box/metadata/discovery/storm-bay.yml &&
  wis2box metadata discovery publish /data/wis2box/metadata/discovery/storm-bay.yml
'
