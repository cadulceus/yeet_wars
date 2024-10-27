FROM node:latest as BUILD

ENV NODE_OPTIONS=--openssl-legacy-provider
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm install
COPY ./ ./
RUN npm run build

FROM nginx:latest

COPY --from=BUILD /build/build /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
