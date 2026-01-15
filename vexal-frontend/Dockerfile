# Use the official NGINX image as the base image
FROM nginx:stable-alpine

# Copy static files from the "dist" directory to NGINX
COPY dist /usr/share/nginx/html

# Expose port 80 for HTTP traffic
EXPOSE 80

# Command to run NGINX
CMD ["nginx", "-g", "daemon off;"]
