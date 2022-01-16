FROM ubuntu:20.04

WORKDIR /root

ENV DEBIAN_FRONTEND noninteractive 
RUN apt update
# RUN apt -y upgrade
RUN apt -y install git build-essential cmake python3-pip gawk flex bison bash gcc-arm-none-eabi

RUN git clone https://github.com/nimo-labs/umake.git -b dev
