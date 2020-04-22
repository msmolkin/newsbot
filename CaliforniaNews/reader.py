#!/usr/bin/env python3
''' TODO
 TODO: turn this into a class.
 TODO probably get rid of the selfposts. They're mostly useless
 content (not news)
 TODO eventually: Also move logging into a separate file
 (and/or a separate class): functions domain_from_url-> str,
 posted_recently -> bool, mark_as_posted -> None
 Change commit message on laptop (misspelled parameter as paramater)
 article_id is for if I can create the convert_article_to_id library/module
'''

''' COMMIT_MSG
    * Added logging CSV file that records every post I've seen so far
    * Also added COVID_19 subreddits to the watched multireddit
    * Dropped Python 2 support by adding parameter types and return types to functions
    *** Replaced the mini "else" commands by putting "if posted_recently) at the beginning of main() (will also remove "if not posted_recently")
'''

import re, datetime
import csv

import praw
import tldextract

reddit = praw.Reddit('californianewsbot')
fieldnames = ['timestamp', 'new_submission_id', 'old_submission_id',
'submission_title', 'duplicate', 'subreddit', 'original_author',
'original_post_date', 'url', 'domain_tld', 'article_id', 'post_text']
LOG_FILE_NAME = "logs/submissions.csv"

# all_subreddits = reddit.subreddit('all')
news_subreddits = multireddit = reddit.subreddit('autonewspaper+california+news+everythingscience+science+full_news+newsstream+upliftingnews+nottheonion+worldnews+truenews+indepthstories+newsporn+truereddit+newsoftheweird+worldnews+business+economics+misha511+covid19+coronavirus')

cities = '[Ss]an [Ff]rancisco|[Ll]os [Aa]ngeles|[Ff]resno|[Bb]erkeley|[Ss]tanford'
regions = 'Silicon Valley|Sonoma County|Napa Valley|Bay Area|Sierra Nevada'
regex = regions + '|' + cities + '|California|[Cc]ali\W|, CA'
site = 'sfgate'
prog = re.compile(regex)

"""
def test_calls():
    # assert that each of these works if it should or doesn't if it shouldn't
    test = "California"; print(test + str(prog.match(test)))
    test = "california"; print(test + str(prog.match(test)))
    test = "Cali"; print(test + str(prog.match(test)))
    test = "cali"; print(test + str(prog.match(test)))
    test = "CA"; print(test + str(prog.match(test)))
    test = "Alberta, Canada"; print(test + str(prog.match(test)))
    test = "San Francisco, CA"; print(test + str(prog.match(test)))
    test = "CARS ARE GOOD"; print(test + str(prog.match(test)))
    test = "we CAn't have this here"; print(test + str(prog.match(test)))
    test = "California"; print(test + str(prog.match(test)))
    test = "califo cali- fo cali"; print(test + str(prog.search(test)))
test_calls()
"""

# NTS: Uses external library. May break if they edit their code.
def domain_from_url(url: str) -> str:
    domain_tld = tldextract.extract(url)
    return domain_tld.domain + '.' + domain_tld.suffix

# todo eventually: move all posts from > 6 weeks ago to "logs/submissions.csv.old"
# which will store old posts, which can be reposted without issues. Also automatically arhcive any posts by programmatically running them through the Wayback Machine at archive.org
def posted_recently(new_submission: praw.models.reddit.submission.Submission) -> bool:
    """ Check whether this submission has been posted recently

    Arguments:
        new_submission {Submission} -- a reddit post

    Returns:
        bool -- whether this post has been added before
        whether the sbmission, or any part of it, is in past submissions. Meant to guarantee no duplicates
    """
    with open("logs/submissions.csv", "r", newline="", encoding="utf-8") as logfile:
        reader = csv.DictReader(logfile, fieldnames)
        for row in reader:
            # NTS: if data was improperly recorded, whole row is read wrong
            logfile_row_domain_tld = row["domain_tld"]
            new_submission_tld = domain_from_url(new_submission.url)

            # TODO@me: modify this to account for inexact matches/titles of different lengths. Possible: take shorter of the two strings, take the last len(shorter) chars of the longer string, and compare them. Should work. I don't have the time atm. Also don't match if it's a new story (e.g. an update to the previous article)
            # Last half of the title from log file
            title_logfile_row = row['submission_title'][len(row['submission_title'])//2:]
            # Last half of title from new submission
            title_submission = new_submission.title[len(new_submission.title)//2:]
            titles_match = title_logfile_row == title_submission
            
            # If URL, check if domains match; else, check post text
            post_link_host_or_text_match = (logfile_row_domain_tld == new_submission_tld or row['post_text'] == new_submission.selftext)

            found = post_link_host_or_text_match and titles_match
            
            if (found):  # new submission already in log file
                # TODO@me: make this work for different length titles: if they're slightly different lengths, then comparing last halfs of the titles directly will be off (i.e. I need to also account for AutoModerator's "[California]"/"[Local]"/"[Global]" posts)
                # TODO: I should probably just remove the tags from the AutoNewspaperAdmin posts: s, t = submission, s.title; if s.author == 'AutoNewspaperAdmin' && t[0] == '[': s.title = t[t.index('-')+ 1:]  # remove autonewspaper category tag
                return True
        return False

def mark_as_posted(old_submission: praw.models.reddit.submission.Submission, new_submission: praw.models.reddit.submission.Submission = None, is_duplicate: bool = False) -> bool:
    """ Add this post to submissions.csv
    
    Arguments:
        old_submission {Submission} -- the submission in question
         If is_duplicate = True  => this is the duplicate submission
         If is_duplicate = False => this is the submission being copied
    
    Keyword Arguments:
        new_submission {Submission} -- the submission being created
         If none is provided, assumes we are not posting because old_submission
         is a duplicate(default: old_submission)
        
        is_duplicate {bool} -- whether old_submission is a duplicate of
                            any past submission (default: False)
    """


    s = old_submission  # Just because I'm too lazy to type it out... I mean, efficiency
    new_submission = new_submission if new_submission else old_submission

    with open(LOG_FILE_NAME, "a", newline="", encoding="utf-8") as logfile:
        writer = csv.DictWriter(logfile, fieldnames)
        
        # Useless; rows added programmatically
        # csv.DictWriter.extrasAction exists, in case I ever need it
        writer.extrasaction = 'ignore'

        submission_info_row = {'timestamp': datetime.datetime.now(),
        'old_submission_id': s.id, 'submission_title': s.title, 'duplicate': False,
        'subreddit': s.subreddit, 'original_author': s.author,
        'original_post_date': s.created_utc, 'new_submission_id': new_submission.id}
        # if not s.is_self, add the URL to the log. Most news posts are links.
        # Otherwise, add the post text
        url = {'url': s.url, 'domain_tld': domain_from_url(s.url)} if s.url else {'post_text': s.selftext}
        submission_info_row.update(url)

        try:
            writer.writerow(submission_info_row)
        except UnicodeEncodeError:  # File opened with utf-8:.shouldn't happen anymore
            del submission_info_row['title']  # deletes offender (title) justincase
            writer.writerow(submission_info_row)

def create_log_file(fname: str) -> None:
    """ Create log files if they do not exist
    
    Arguments:
        fname {str} -- the name of the log file
    """

    DIR = "logs/"
    if not fname.startswith(DIR):
        raise ValueError("Log file in not in proper subdirectory: logs/")
    
    # Regular log file
    fname_regular = fname
    # Old posts file for files > 6 mo.
    fname_old = fname + ".old"
    for fname in fname_regular, fname_old:
        try:
            f = open(fname, "r")
            f.close()
        except IOError:
            with open(fname, "w", newline="") as f:  # why newline=""? see python.org/docs
                writer = csv.DictWriter(f, fieldnames)
                writer.writeheader()

# Assuming this works
def main():
    create_log_file(LOG_FILE_NAME)
    print(f"Began posting at {datetime.datetime.now()}")

    # todo eventually maybe: since the limit is 100 posts *per API call,*
    # and API calls are limited to 60 per minute, how about calling
    # each subreddit separately?
    # for subreddit_name in str(news_subreddits).split('+')
    #   for submission in reddit.subreddit(subreddit_name)
    # Except not like that ^ (more "simultaneously" so they flow in chronological order). Not important at all, since this only matters when the bot is starting. Once it's running, the stream checks all the subreddits together, anyway
    for submission in news_subreddits.stream.submissions():
        if prog.search(submission.title):
            if posted_recently(submission):
                mark_as_posted(submission, is_duplicate=True)
            else:  # new post
                copied_submission = submission
                if copied_submission.is_self:  # text-post                             # TODO: probably just `pass` on these instead of copying them, or (IDEA) link to the original post. Not usually worth being news. I'll check the logs later to see which I should do. Data is power, and I don't have the data yet to make the proper decision.
                    new_submission = reddit.subreddit('CaliforniaNews').submit(copied_submission.title, selftext=copied_submission.selftext, send_replies=False) # or it could crosspost to r/californianews
                    mark_as_posted(copied_submission, new_submission)
                else:  # link post
                    new_submission = reddit.subreddit('CaliforniaNews').submit(copied_submission.title, url=copied_submission.url, send_replies=False) # or it could crosspost to r/californianews
                    mark_as_posted(copied_submission, new_submission)
        #else: print(f"Skipped {submission.title[:100]}...")
#f.close()

if __name__ == '__main__':
    main()
