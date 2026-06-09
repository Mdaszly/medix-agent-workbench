FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ARG VITE_API_BASE=http://127.0.0.1:8012
ENV VITE_API_BASE=$VITE_API_BASE

RUN npm run build

EXPOSE 4178

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0"]
