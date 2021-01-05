Flask App Demo

Description:
Flask App ready to deploy on Heroku

Features:
- Adding orders and products to a database
- Usage of fullcalendar.io V5
- Usage of eBay search API

Usage of eBay search API:
Takes a list of product in a .txt file. The list in the file must be of this structure for each line:
"search keywords", (minimum price), (product cost in USD)

Like on eBay, it is possible to include operaters like '-' to filter results in the keywords.

The minimum price can be at 0 and it is only used to filter results as needed. Example: Searching for a pair of headphones
might lead to getting results for the headphones cable which costs less. So adding a minimum price around the expected price
will lead to better search results.

The product cost is what would the the cost by unit if bought from a distributor in the US.