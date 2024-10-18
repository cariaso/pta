aws --profile personal s3 cp mypdf1.pdf  s3://cariaso.com/2024/somerset/pta/latest-somerset-directory.pdf
uv run ./make_directory.py make-all-pdfs --src StudentDirectory2024.xlsx 
