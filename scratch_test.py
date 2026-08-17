import plotly.express as px
import plotly.io as pio
import pandas as pd
import traceback
import concurrent.futures
import time

def test():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    fig = px.line(df, x="A", y="B")
    
    def generate(i):
        return pio.to_image(fig, format="png")
        
    try:
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(generate, i) for i in range(8)]
            results = [f.result(timeout=20) for f in concurrent.futures.as_completed(futures)]
        print(f"Success! Generated {len(results)} images in {time.time()-start:.2f}s")
    except Exception as e:
        print("Failed to generate images:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
