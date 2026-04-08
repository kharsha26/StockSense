FROM node:18

WORKDIR /app

COPY package.json .
RUN npm install

ENV HOST=0.0.0.0

COPY . .

EXPOSE 3000

CMD ["npm", "start"]