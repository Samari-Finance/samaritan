# Samaritan
# Copyright (C) 2021 Samari.finance
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# ---------------------------------------------------------------------

# syntax=docker/dockerfile:1
FROM python:3.8-slim-buster
WORKDIR /bot
COPY requirements.txt requirements.txt
COPY . .
RUN apt-get update && apt-get install -y git
RUN pip3 install -r requirements.txt
CMD [ "python3", "-m" , "main", "--host=0.0.0.0"]