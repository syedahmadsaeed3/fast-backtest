# Running locally

This project requires Python 3.8 version or above

Create a
[virtual environment](https://docs.python.org/3/tutorial/venv.html) to run the
application.

## Requirements for TA-Lib

### Linux

These commands are necessary before installing the Python TA-Lib to make sure the C is compiled first:

```bash
    apt-get update \
    && apt-get install gcc python3-dev python-dev -y \
    && apt-get install -y make \
    && apt install build-essential -y\
    && apt-get install wget -y\
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz\
    && tar -xzvf ta-lib-0.4.0-src.tar.gz\
    && cd ta-lib\
    && ./configure --prefix=/usr\
    && make \
    && make install
```

### Mac

```bash
 brew install ta-lib
```

After running the platform specific TA-Lib code above, run:

```bash
cd [repository root]

source /path/to/virtualenv/bin/activate  # use this if virtual enviroment is setup

pip3 install -r requirements.txt
```

### Adding new dependencies to requirements.txt

In the project directory, avoid using `pip freeze` to populate requirements.txt because that may pollute the file with local dependencies that are not related to the project.

Rather, consider using `pipreqs` as well as adding dependencies one at a time to improve ease of upgrading

```
 pip install pipreqs
 pipreqs .
```

### Setup Database

Create an empty database in postgresql name as `vectorbt`

Run the following command to run the migrations:

```bash
cd [repository root]

source /path/to/virtualenv/bin/activate  # use this if virtual enviroment is setup

alembic upgrade head
```

Ticker model migrations not included, since alembic migration command does not create correct migration for `ts_vector` field. This model will automatically be created the first time project is run

To create new migrations, make sure the model has been imported inside the env.py file in alembic directory and run the following command:

```bash
cd [repository root]

source /path/to/virtualenv/bin/activate  # use this if virtual enviroment is setup

alembic revision --autogenerate -m"<message>"
```

After installing the requirements and setting up the database, FastAPI project can be run using the following command:

```bash
cd [repository root]

source /path/to/virtualenv/bin/activate  # use this if virtual enviroment is setup

uvicorn main:web_app --reload
```

### Updating tickers
make sure that all the migrations have been run.
to run the script, cd to root directory, activate the virtual env and run the following command:
```bash
python update_tickers.py
```
