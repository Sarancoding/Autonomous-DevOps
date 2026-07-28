# ---- Build Stage ----
FROM node:20-alpine AS builder

WORKDIR /build
COPY package.json .
RUN npm install

COPY . .
RUN npm run build

# ---- Serve Stage ----
FROM nginx:alpine

COPY --from=builder /build/dist /usr/share/nginx/html
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen       5173;
    server_name  localhost;

    root   /usr/share/nginx/html;
    index  index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }

    location /ws {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
