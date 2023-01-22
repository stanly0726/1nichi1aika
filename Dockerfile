FROM python:3.9.2-alpine as base
FROM base as builder
# WORKDIR /ffmpeg
# RUN wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz && \
#     tar xvf ffmpeg-git-amd64-static.tar.xz && \
#     cd * && \
#     mv ffmpeg ..

COPY requirements.txt /requirements.txt
RUN pip install --user -r /requirements.txt

FROM base
RUN apk add  --no-cache ffmpeg
# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
# COPY --from=builder /ffmpeg/ffmpeg /usr/local/bin

COPY aika.py /app/aika.py
WORKDIR /app

# update PATH environment variable
ENV PATH=/home/app/.local/bin:$PATH

CMD ["python", "aika.py"]