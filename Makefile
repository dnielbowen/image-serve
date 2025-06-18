# Be sure to change the ROOT first in app.py
serve:
	flask run --host=0.0.0.0 --port=5050

generate_index:
	python3 generate_index.py \
		/home/daniel/backup/20250617_iMessage \
		image_index.json
