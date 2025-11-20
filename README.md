This entire project is built in Gitpod cloud environment using:

- FastAPI
- Postgres (NeonDB)
- Redis (Upstash)
- Docker + docker-compose
- Celery
- GitHub Actions CI/CD
- Deployed to Render
  No local installations required.

Add “Getting Started” section describing docker-compose up

Mention that project runs in Gitpod/Cloud

Add “Stack” section listing FastAPI, Postgres, Redis, Celery, Docker etc.




To rebuild Docker :-

docker-compose down
docker-compose up --build

To check error while running fastapi:-

docker-compose logs api --tail=20
