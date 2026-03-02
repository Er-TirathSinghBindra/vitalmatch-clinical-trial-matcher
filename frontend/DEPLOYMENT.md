# Frontend Deployment Guide

This guide covers deploying the VitalMatch frontend to AWS S3 and CloudFront.

## Prerequisites

- AWS CLI installed and configured
- AWS account with appropriate permissions
- Backend API Gateway endpoint deployed and accessible

## Step 1: Configure Environment

1. Create `.env` file in the frontend directory:
   ```bash
   cp .env.example .env
   ```

2. Update the API endpoint in `.env`:
   ```
   VITE_API_ENDPOINT=https://your-api-gateway-id.execute-api.us-east-1.amazonaws.com/prod
   ```

## Step 2: Build the Application

Build the production bundle:

```bash
cd frontend
npm install
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Step 3: Create S3 Bucket

Create an S3 bucket for static website hosting:

```bash
aws s3 mb s3://vitalmatch-frontend --region us-east-1
```

Enable static website hosting:

```bash
aws s3 website s3://vitalmatch-frontend \
  --index-document index.html \
  --error-document index.html
```

## Step 4: Configure Bucket Policy

Create a bucket policy file `bucket-policy.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::vitalmatch-frontend/*"
    }
  ]
}
```

Apply the policy:

```bash
aws s3api put-bucket-policy \
  --bucket vitalmatch-frontend \
  --policy file://bucket-policy.json
```

## Step 5: Upload Build Files

Upload the build files to S3:

```bash
aws s3 sync dist/ s3://vitalmatch-frontend --delete
```

Set proper cache headers for static assets:

```bash
# Cache CSS and JS files for 1 year
aws s3 cp s3://vitalmatch-frontend s3://vitalmatch-frontend \
  --recursive \
  --exclude "*" \
  --include "*.css" \
  --include "*.js" \
  --metadata-directive REPLACE \
  --cache-control "max-age=31536000,public"

# Don't cache HTML files
aws s3 cp s3://vitalmatch-frontend s3://vitalmatch-frontend \
  --recursive \
  --exclude "*" \
  --include "*.html" \
  --metadata-directive REPLACE \
  --cache-control "no-cache,no-store,must-revalidate"
```

## Step 6: Create CloudFront Distribution

Create a CloudFront distribution configuration file `cloudfront-config.json`:

```json
{
  "CallerReference": "vitalmatch-frontend-2024",
  "Comment": "VitalMatch Frontend Distribution",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "S3-vitalmatch-frontend",
        "DomainName": "vitalmatch-frontend.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-vitalmatch-frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"]
    },
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CustomErrorResponses": {
    "Quantity": 1,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "Enabled": true
}
```

Create the distribution:

```bash
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json
```

Note the distribution ID and domain name from the output.

## Step 7: Request SSL Certificate (Optional)

If using a custom domain:

1. Request a certificate in ACM (must be in us-east-1 for CloudFront):
   ```bash
   aws acm request-certificate \
     --domain-name vitalmatch.example.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. Validate the certificate via DNS

3. Update CloudFront distribution to use the certificate

4. Create Route 53 alias record pointing to CloudFront

## Step 8: Associate WAF with CloudFront

Associate the WAF Web ACL created in the infrastructure setup:

```bash
aws cloudfront update-distribution \
  --id YOUR_DISTRIBUTION_ID \
  --web-acl-id YOUR_WAF_ACL_ARN
```

## Step 9: Test the Deployment

1. Access the CloudFront URL:
   ```
   https://d1234567890abc.cloudfront.net
   ```

2. Verify the application loads correctly

3. Test form submission and API connectivity

4. Check browser console for errors

5. Test on mobile devices

## Continuous Deployment Script

Create a deployment script `deploy.sh`:

```bash
#!/bin/bash

set -e

echo "Building frontend..."
npm run build

echo "Uploading to S3..."
aws s3 sync dist/ s3://vitalmatch-frontend --delete

echo "Setting cache headers..."
aws s3 cp s3://vitalmatch-frontend s3://vitalmatch-frontend \
  --recursive \
  --exclude "*" \
  --include "*.css" \
  --include "*.js" \
  --metadata-directive REPLACE \
  --cache-control "max-age=31536000,public"

aws s3 cp s3://vitalmatch-frontend s3://vitalmatch-frontend \
  --recursive \
  --exclude "*" \
  --include "*.html" \
  --metadata-directive REPLACE \
  --cache-control "no-cache,no-store,must-revalidate"

echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"

echo "Deployment complete!"
```

Make it executable:

```bash
chmod +x deploy.sh
```

Run deployment:

```bash
./deploy.sh
```

## Rollback Procedure

If you need to rollback to a previous version:

1. Enable S3 versioning on the bucket:
   ```bash
   aws s3api put-bucket-versioning \
     --bucket vitalmatch-frontend \
     --versioning-configuration Status=Enabled
   ```

2. List object versions:
   ```bash
   aws s3api list-object-versions --bucket vitalmatch-frontend
   ```

3. Restore previous version:
   ```bash
   aws s3api copy-object \
     --bucket vitalmatch-frontend \
     --copy-source vitalmatch-frontend/index.html?versionId=VERSION_ID \
     --key index.html
   ```

4. Invalidate CloudFront cache

## Monitoring

Monitor the frontend deployment:

1. **CloudFront Metrics**: Check in CloudWatch
   - Requests
   - Bytes downloaded
   - Error rate
   - Cache hit ratio

2. **S3 Metrics**: Monitor bucket access
   - Request count
   - Bytes downloaded
   - 4xx/5xx errors

3. **WAF Metrics**: Check blocked requests
   - Blocked requests count
   - Allowed requests count
   - Rule matches

## Troubleshooting

### Issue: 404 errors on page refresh

**Solution**: Ensure CloudFront custom error response redirects 404 to index.html

### Issue: Old content still showing

**Solution**: Invalidate CloudFront cache:
```bash
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Issue: API calls failing

**Solution**: 
- Check CORS configuration on API Gateway
- Verify API endpoint in .env file
- Check browser console for CORS errors

### Issue: Slow loading times

**Solution**:
- Enable CloudFront compression
- Optimize image sizes
- Check cache headers are set correctly

## Cost Optimization

- Enable CloudFront compression to reduce data transfer
- Set appropriate cache TTLs to reduce origin requests
- Use S3 Intelligent-Tiering for cost savings
- Monitor CloudFront usage and adjust as needed

## Security Checklist

- ✅ HTTPS enforced via CloudFront
- ✅ WAF rules active
- ✅ S3 bucket not publicly listable
- ✅ CloudFront access logging enabled
- ✅ API endpoint uses HTTPS
- ✅ No sensitive data in frontend code
- ✅ Environment variables properly configured

## Next Steps

After deployment:

1. Set up CloudWatch alarms for errors
2. Configure CloudFront access logging
3. Set up automated deployments via CI/CD
4. Monitor user analytics
5. Test performance with real users
