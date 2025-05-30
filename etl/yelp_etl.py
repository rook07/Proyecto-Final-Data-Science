import pandas as pd
import warnings
import re

warnings.filterwarnings("ignore")
business= pd.read_csv(r'C:\Users\ruizr\Desktop\datos\yelp\business.csv')

business = business.loc[:, ~business.columns.str.endswith('.1')]

resto_business = business[business['categories'].apply(
    lambda x: (
        bool(re.search(r'fast food', x, re.IGNORECASE)) and
        bool(re.search(r'burger|hamburger', x, re.IGNORECASE))
    ) if isinstance(x, str) else False
)]

resto_business = resto_business[resto_business["state"].isin(["CA"])]

resto_business = resto_business.drop(columns=['is_open',"hours","postal_code","hours","stars","review_count","state","address","categories"])

chunks = pd.read_json(r"C:\Users\ruizr\Desktop\datos\yelp\review.json", lines=True, chunksize=1000000)
review = pd.concat(chunks, ignore_index=True)

review['date'] = review['date'].dt.normalize()
review_yelp= review[review["date"] >= "2016-01-01"]
duplicados = review.duplicated().sum()
review.drop_duplicates(inplace=True)
review = review.drop(["funny", "cool", "useful"], axis=1)
review_fastyelp = review_yelp.merge(resto_business,on="business_id",how="inner")
review_fastyelp.drop(["business_id"], axis=1, inplace=True)