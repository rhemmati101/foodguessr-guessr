for i in $(seq 1 $1); do
     echo "Scraping attempt $i..."
    python3 scrape.py
    sleep 3
done