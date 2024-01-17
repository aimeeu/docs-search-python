<!---
.. ===============LICENSE_START=======================================================
.. Armory CC-BY-4.0
.. ===================================================================================
.. Copyright (C) 2021 Armory. All rights reserved.
.. ===================================================================================
.. This documentation file is distributed by Armory
.. under the Creative Commons Attribution 4.0 International License (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
.. http://creativecommons.org/licenses/by/4.0
..
.. This file is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.
.. ===============LICENSE_END=========================================================
-->

# docs-search

- Uses the ServiceNow API to get Armory Knowledge Base articles
- Parses the results and puts into a format that Elastic Cloud App Search understands
- Uses the Elastic App Search API to push the articles to Armory's Elastic Cloud App Search engines
- Runs as a Kubernetes job. API keys are stored as Kubernetes secrets.
- Armory used a GitHub Action to push the containerized app to GitHub Container Registry

## Prerequisites

Docker

## Developer setup

- clone the repo

## Run the job in a container

From the `docs-search` directory:

```
docker build -t armory/docs-search-updater .
## API_PRIVATE_KEY is the ElasticSearch API key for posting data.
docker run --env API_PRIVATE_KEY=replaceme -it <image>
```

## Resources

- https://www.elastic.co/guide/en/enterprise-search-clients/python/current/index.html
- https://docs.servicenow.com/bundle/paris-application-development/page/integrate/inbound-rest/concept/knowledge-api.html#knowledge-management-api

## Architecture

- `properties.json`:
   - `serviceNow.apiUrl`:  API endpoint; either dev (armory-dev.service-now.com...) or prod (armory.service-now.com...)
   - `serviceNow.fetchLimit`: number of articles to fetch; default set by ServiceNow is 30
   - `serviceNow.articleUrlBase`: KB articles base URL; this is not part of the `link` field that the API provides
   - `elasticAppSearch.apiUrl`: base API url for our Elastic Cloud instance
   - `elasticAppSearch.postSizeLimit`: App Search limits the number of articles you can post in a single API call. This field is the size limit and is used by the code to split the article payload
   - `elasticAppSearch.engines`: list of engines to POST to
- `models.py`:
   - contains the `Properies` class
- `app.py`:
   - This file fetches KB articles, formats the data, and then posts to Elastic.
   - Logging: RotatingFileHandler appender writes to `kb-job.log`; StreamHandler write to sys.stdout 
