echo "Deploying Frontend..."
cd frontend
export REACT_APP_API_URL=/api
npm run build
aws s3 sync out/ s3://bluebook-ai-frontend --acl public-read
