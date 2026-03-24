FROM node:20-alpine AS build
WORKDIR /app
# Browser-reachable API origin (NOT the internal Docker service name unless users run browsers inside the stack).
ARG REACT_APP_PHI_DPS_API_BASE=http://127.0.0.1:8000
ENV REACT_APP_PHI_DPS_API_BASE=$REACT_APP_PHI_DPS_API_BASE
COPY web/package*.json ./
RUN npm install
COPY web/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
