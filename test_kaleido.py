import plotly.express as px
import plotly.io as pio
import pandas as pd
import traceback

def test():
    df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    fig = px.line(df, x="A", y="B")
    try:
        img = pio.to_image(fig, format="png")
        print("Success! Image size:", len(img))
    except Exception as e:
        print("Failed to generate image:")
        traceback.print_exc()

if __name__ == "__main__":
    test()
