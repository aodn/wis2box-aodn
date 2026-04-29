# Walkthrough -- Publishing WIS2 Data

## 1. Setup MQTT Explorer
Install MQTT Explorer: https://mqtt-explorer.com/


### Add Connection to IMOS WIS2 node:
Connect to Global Broker:
```
Broker: globalbroker.meteo.fr
Port: 8883
Username: everyone
Password: everyone
```
add Subscrition Topic: `origin/a/wis2/#` by clicking `ADVANCED` button


Connect IMOS-WIS2 node on Non-Production env:
```
Broker: wis2box-broker.edge.aodn.org.au
Port: 1883
Username: wis2box
Password: [copy it from AWS Secrets Manager Parameter Store]
```
Production env is same as Non-Production env, just change the broker name to `Broker: wis2box-broker.production.aodn.org.au`. Here, we use non-production env for the workshop.


How to copy the password:

1. Go to AWS console
2. Go to [Secrets Manager](https://ap-southeast-2.console.aws.amazon.com/systems-manager/home?region=ap-southeast-2#welcome)
3. Go to Parameter Store
4. Search `wis2`
5. Select the secret `/apps/wis2box/edge/mosquitto_broker_password`
6. Copy the value



## 2. Publish dataset discovery metadata
1. Manually publish dataset discovery metadata

```
Topic: `publication/dc/a/wis2/aus/imos/metadata/dataset/
```


## 3. Publish station metadata

1. Method 1. Manually publish station metadata 
```
Topic: 
```

Referring to the `station_list.csv` file

```csv
station_name,wigos_station_identifier,traditional_station_identifier,facility_type,latitude,longitude,elevation,barometer_height,territory_name,wmo_region
LEOLIS-BAY,0-22000-0-5501882,5501882,seaFixed,-43.2308,147.4589,0,0,AUS,southWestPacific
```


Note: Admin should ensure the Token is prepared for the workshop.
```
wis2box auth add-token --path processes/wis2box

wis2box auth add-token --path collections/stations
```






## 4. Publish data
