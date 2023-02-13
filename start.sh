docker container stop producer_app > /dev/null 2>&1
docker container rm producer_app > /dev/null 2>&1

docker container stop consumer_app > /dev/null 2>&1
docker container rm consumer_app > /dev/null 2>&1

docker compose build
docker compose up
