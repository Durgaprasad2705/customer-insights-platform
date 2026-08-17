import plotly.express as px
import plotly.io as pio
import pandas as pd
import traceback
import concurrent.futures

def test():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    fig = px.line(df, x="A", y="B")
    
    def generate():
        return pio.to_image(fig, format="png")
        
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(generate)
            img = future.result(timeout=10)
        print("Success! Image size:", len(img))
    except Exception as e:
        print("Failed to generate image:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
