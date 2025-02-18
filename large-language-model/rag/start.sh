docker run --name pgvector \
--rm -it -p 5432:5432 \
-e POSTGRES_USER=postgres \
-e POSTGRES_PASSWORD=postgres \
ankane/pgvector