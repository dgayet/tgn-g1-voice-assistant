docker run --name chatbotx --network=host --runtime=nvidia -v /dev:/dev --privileged --env=".env" -it gemini-image:latest /bin/bash
