FROM node:22-slim AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./

# Vite bakes VITE_* into the JS bundle at build time. The browser (running on
# the host, not inside the Docker network) reaches the backend via its
# published host port, so this stays localhost even though the frontend
# itself is containerized.
ARG VITE_API_BASE=http://localhost:8005
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
