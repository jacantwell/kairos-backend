## User requirements

Sign-up

Define a `journey`
    Add a current location to a `journey`
    Add a future location to a `journey`

## Technical thoughts

### Potential routes

users/{user_id}

### Mongo stuff

Will need to create geo spatial indexs for location data, e.g:

```
// For the historic route
db.journeys.createIndex({ "route_history.coordinates": "2dsphere" })

// For the planned route
db.journeys.createIndex({ "planned_route.coordinates": "2dsphere" })
```




