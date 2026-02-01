# 构建器
FROM --platform=$BUILDPLATFORM docker.io/docker/docker-ce:20.10.0 AS buildx

RUN docker buildx create --use --name multiarch

# 构建ARM64镜像
FROM buildx AS edge
ARG BUILDPLATFORM
COPY Dockerfile.arm64 /
RUN echo "Building for $BUILDPLATFORM" && \
    $BUILDPLATFORM=linux/arm64 docker buildx build --platform linux/arm64 -t mimage --load .

# 最后阶段 
# 最后阶段
FROM edge AS final  
COPY --from=mimage / /

# 安装Edge浏览器
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/microsoft.list && \
    apt-get update && \
    apt-get install -y microsoft-edge-dev

# 设置为默认浏览器
ENV BROWSER="microsoft-edge"
