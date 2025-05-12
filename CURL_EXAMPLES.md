# Testing with ``curl``

See the [stage0_py_utils CURL Examples](https://github.com/agile-learning-institute/stage0_py_utils/blob/main/CURL_EXAMPLES.md) for stage0 standard endpoints

- [/api/chain endpoints](#apichain-endpoints)
     - [GET /api/chain](#get-a-list-of-all-exercise-chains)
     - [GET /api/chain/{id}](#get-a-single-exercise-chain)

- [/api/exercise endpoints](#apiexercise-endpoints)
     - [GET /api/exercise](#get-a-list-of-all-active-exercises)
     - [GET /api/exercise/{id}](#get-a-single-exercise)

- [/api/workshop endpoints](#apiworkshop-endpoints)
     - [GET /api/workshop](#get-a-list-of-all-active-workshops-by-workshop-name-regex)
     - [POST /api/workshop](#add-a-new-workshop)
     - [GET /api/workshop/{id}](#get-a-specific-workshop)
     - [PATCH /api/workshop/{id}](#update-a-workshop)
     - [POST /api/workshop/{id}/start](#start-a-workshop---status-to-active)
     - [POST /api/workshop/{id}/next](#advance-to-the-next-exercise-in-the-workshop)
     - [POST /api/workshop/{id}/observation](#add-an-observation-to-the-current-exercise)
     
## /api/chain endpoints 

#### Get a list of all Exercise Chains
```sh
curl http://localhost:8580/api/chain
```
#### Get a single Exercise Chain
```sh
curl http://localhost:8580/api/chain/a00000000000000000000001
```

## /api/exercise endpoints

#### Get a list of all active exercises
```sh
curl http://localhost:8580/api/exercise
```
#### Get a single exercise
```sh
curl http://localhost:8580/api/exercise/b00000000000000000000001
```

## /api/workshop endpoints

#### Get a list of all active workshops by workshop name regex
```sh
curl "http://localhost:8580/api/workshop"
```
#### Get a list of workshops by workshop name regex
```sh
curl "http://localhost:8580/api/workshop?query=^p"
```
#### Get a specific workshop
```sh
curl "http://localhost:8580/api/workshop/000000000000000000000001"
```
#### Add a new Workshop
```sh
curl -X POST http://localhost:8580/api/workshop/new/a00000000000000000000001 \
     -H "Content-Type: application/json" \
     -d '{"name":"Super Duper Workshop"}'
```
#### Update a workshop
```sh
curl -X PATCH http://localhost:8580/api/workshop/000000000000000000000001 \
     -H "Content-Type: application/json" \
     -d '{"name":"Updated Workshop Name"}'
```
#### Start a workshop - Status to active
```sh
curl -X POST http://localhost:8580/api/workshop/000000000000000000000001/start
```
#### Advance to the next exercise in the workshop
```sh
curl -X POST http://localhost:8580/api/workshop/000000000000000000000001/next
```
#### Add an observation to the current exercise
```sh
curl -X POST http://localhost:8580/api/workshop/000000000000000000000001/observation \
     -H "Content-Type: application/json" \
     -d '{"name":"Observation1"}'
```
