# Theory

Cultural phenomena are rich in meaning and context.
Moreover, the meaning and context are what we care about, so stripping that would be a disservice.

Consider Geertz:

> Not only is the semantic structure of the figure a good deal more complex than it appears on the surface, but an analysis of that structure forces one into tracing a multiplicity of referential connections between it and social reality, so that the final picture is one of a configuration of dissimilar meanings out of whose interworking both the expressive power and the rhetorical force of the final symbol derive. (Geertz [1955] 1973, Chapter 8 Ideology as a Cultural System, p. 213)

The way people understanding their world shape their action, and understandings are heterogeneous in any community, woven into a complex web of interacting pieces and parts.
Understandings are constantly evolving, shifting with every conversation or Breaking News.
Any quantitative technique for studying meaning must be able to capture the relational structure of cultural objects, their temporal dynamics, or it cannot be meaning.

These considerations motivate how I have designed the data structure and code for this project.
My attention to "cooccurrences" in what follows is an application of Levi Martin and Lee's (2018) formal approach to meaning.
They develop the symbolic formalism I use below, as well as showing several general analytic strategies for inductive, ground-up meaning-making from count data.
This approach is quite general, useful for many applications.

The process is rather simple, I count cooccurrences between various attributes.
For each document, for each citation in that document, I increment a dozen counters, depending on attributes of the citation, paper, journal, or author.
This counting process is done once, and can be used as a compressed form of the dataset for all further analyses.
In the terminology of Levi Martin and Lee, I am constructing "hypergraphs", and I will use their notation in what follows.
For example $[c*fy]$ indicates the dataset which maps from $(c, fy) \to count$.

$c$ is the name of the cited work.
$fy$ is the publication year of the article which made the citation.
$count$ is the number of citations which are at the intersection of these properties.

+ $[c]$ the number of citations each document receives
+ $[c*fj]$ the number of citations each document receives from each journal's articles
+ $[c*fy]$ the number of citations each document receives from each year's articles
+ $[fj]$ the number of citations from each journal
+ $[fj*fy]$ the number of citations in each journal in each year
+ $[t]$ cited term total counts
+ $[fy*t]$ cited term time series
+ term cooccurrence with citation and journal ($[c*t]$ and $[fj*t]$)
+ "author" counts, the number of citations by each author ($[a]$ $[a*c]$ $[a*j*y]$)
+ $[c*c]$, the cooccurrence network between citations
+ the death of citations can be studied using the $[c*fy]$ hypergraph
+ $[c*fj*t]$ could be used for analyzing differential associations of $c$ to $t$ across publication venues
+ $[ta*ta]$, $[fa*fa]$, $[t*t]$ and $[c*c]$ open the door to network-scientific methods

# How to retrieve the requisite data

+ This notebook generates cooccurrence counts given Web of Science output.
+ No Web of Science output is included in knowknow in compliance with Web of Science terms of use.
+ **This notebook is only useful if you have your own Web of Science output**, and want to run analyses on that.

Data can be downloaded from any Web of Science search results page:
1. `Export -> Other File Formats`. 
2. In the dropdowns, specify `Record Content -> Full Record and Cited References` and `File Format -> Tab Delimited (Win)`
3. Type the folder containing the saved records as `.txt` files into the variable `wos_base` below.