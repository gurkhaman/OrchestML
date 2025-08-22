## Repository Service
The **Repository Service** is responsible handling all the services (ML and otherwise) that will be utilized for creating compositions.
Its job is to act as the repository.
The repository by itself doesn't contain the actual service artifacts, instead it contains the service descriptions of services found in external hubs such as HuggingFace, ROS Index, or Github.
The repository is responsible for the following:

1. Hosting the vector DB that we can RAG with.
2. Manage documents (service descriptions) that will be handled by the vector DB.
3. Manage the embedding function.
4. Manage the similarity/relevance function (used for RAG).

### Vector DB
We utilize ChromaDB as our vector DB.
Configuration for ChromaDB can be found in the `configs` directory.

### Services and Service Descriptions
We have manually gathered a set of services from multiple external hubs for testing and evaluation purposes. 
Service descriptions of these external services can be found in the `data` directory.

### Embedding Function
We utilize Hugging Face's text embedding model to turn the service descriptions into vector representations.

### Similarity/Relevance Function
We use cosine similarity for our similarity function.