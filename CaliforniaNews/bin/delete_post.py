import praw, sys
id = sys.argv[1] if len(sys.argv) > 1 else input("Which post to delete? ")
praw.Reddit('californianewsbot').submission(id).delete()
