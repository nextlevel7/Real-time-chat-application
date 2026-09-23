# Stage 1: Build the Angular application
FROM node:22-slim AS build

WORKDIR /app

# Install dependencies based on lockfile
COPY package*.json ./
RUN npm ci

# Copy source and build production bundle
COPY . .
RUN npm run build -- --configuration production

# Stage 2: Serve application with Nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
