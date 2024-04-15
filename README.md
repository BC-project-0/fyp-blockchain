# fyp-blockchain
Blockchain implementaion - Final Year Project

docker build -t fyp .  
docker run -d -v fyp-store:/app/data --name fyp -e NODE_ID=1 -p 80:80 fyp