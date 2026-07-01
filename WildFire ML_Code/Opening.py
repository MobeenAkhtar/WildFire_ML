from pathlib import Path
import webbrowser


#*******************
#Opening both results
#*******************

map = Path('WildFire ML/Result/Map_representation.html').resolve()
graph = Path('WildFire ML/Result/Graph_representation.html').resolve()

webbrowser.open(map.as_uri())
webbrowser.open(graph.as_uri())
