FROM golang:1.23

ENV     SRC=/go/src/github.com/chr0n1x/go-tallest
WORKDIR $SRC
COPY    src/ $SRC/src
ADD     go.mod $SRC

RUN go build -o /go/bin/tallest ./src

ENTRYPOINT /go/bin/tallest
