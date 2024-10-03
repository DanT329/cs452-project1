# cs452-project1

This database is used to track a company's tools. Things like location, condition, and maintenance records. 

 

 I tried a Single-domain Few-shot Text-to-SQL and Zero-shot Text-to-SQL approach. 

 

For the Zero-shot Text-to-SQL, answers were generally fine but sometimes lacked needed information. For example, on one question: “Do employees have any tools checked out that have not been serviced in the last two months?” On some occasions, the response would exclude tools that have never been serviced. The LLM never “thought” to add anything that wasn’t specifically defined. 

 

For Single-domain Few-shot Text-to-SQL, the responses had more information usually but would format strangely. Like if the example prompt didn’t return a serial number for a tool, then neither would GPT 4.o mini.  

 

Overall, single domain gives more complete data when provided a few examples but will then run into the issue of following the formatting of the examples so closely as to give sometimes strange results. 
