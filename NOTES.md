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

User Requirements 2:

User can see other bikepackers near their route.
    - This helps load on server as we do not need to display all user journeys to every user.
    - If a user adds a point to their route, their view is updated -> shows them other users near this point.
    - If a user adds a point to their route, other user views are updated -> the user's route may now be visible to more users.

A user's journey consists of journey markers and plan markers (coord points)

The journey markers show where the user has been and the plan markers show where the user plans to go.

If a user wishes they can just use journey markers to show where they have been.

Alternatively they can start with a full route of plan marker of which they can then convert them to journey markers as they travel.

They should also be able to insert a journey marker before the next plan marker.

Tech details

Marker data will be stored in a mongoDb database using geo spatial indexes for optimisation.
The database just needs to manage marker data, any drawing between these markers can happen on the frontend.

A 'Journey' must have a unique ID - There will be a page where a user names their journey before adding markers.

Initial thoughst on api routes:

POST journeys/  // Create a new Journey
GET journeys/{journey-id}   // Get the metadata of a Journey, name, desc, ...

POST journeys/{journey-id}/plan     // Adds a new plan marker
POST journeys/{journey-id}/marker   // Adds a new journey marker

GET journeys/{journey-id}/neighbours    // Returns the journey IDs of all other user journies deemed     
                                        // close to {journey-id}

GET journeys/{journey-id}/markers   // Returns all markers (plan+journey) of a journey






