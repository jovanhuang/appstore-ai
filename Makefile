init_repo:
	@echo "Getting latest version of repository"
	git fetch && git pull
	@echo "Setting default commit template"
	git config --local commit.template .github/ct.md

create_venv:
	@echo "Setting up virtual environment"
	python -m venv venv
	source ./venv/bin/activate
	@echo "Installing poetry"
	pip install poetry

install: poetry.lock
	@echo "Installing dependencies"
	source ./venv/bin/activate
	poetry install

setup: create_venv install

init_server: 
	. venv/bin/activate && mlaunch init --single --port 27017 --name "app_store";\

start_server: 
	@echo "Starting MongoDB"
	-@if [ -d "data" ];then\
		. venv/bin/activate && mlaunch start;\
	else\
		echo "No mlaunch data, run make init_server";\
	fi

stop_server:
	@echo "Stopping MongoDB"
	@if [ -d "data" ];then\
		. venv/bin/activate && mlaunch stop;\
	else\
		echo "No mlaunch data, run make init_server";\
	fi
