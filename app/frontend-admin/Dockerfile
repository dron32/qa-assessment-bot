FROM node:20-alpine

WORKDIR /app

# Копируем package.json и устанавливаем зависимости
COPY package*.json ./
RUN npm install

# Копируем исходный код
COPY . .

# Собираем приложение
RUN npm run build

EXPOSE 5173

# Запускаем dev-сервер для разработки
CMD ["npm", "run", "dev"]





