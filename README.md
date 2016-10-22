# Auto-REST

Goal:
- write web (and mobile?) apps without writing a back-end
- REST
- easy defaults
- support users and permissions
  - "users can't edit each others' posts"
  - "newPost.authorId === currentUser.id"
  - "users can't detect the existence of each others' private messages"
- support schema validation
  - "bad request: got an unexpected parameter"
  - "bad request: expected a string but got an object"


By default, the client can CRUD anything from any collection!
Later, you can add permission and validation one collection at a time.
Maybe you can even profile the app to determine what rules to whitelist.

Implementation ideas:
- implement permissions using "views", sort of
  - each collection can have a user-specific filter, an agg prefix.
- use Python because I'm familiar with it
  - but make the framework language-independent:
    - don't allow writing extensions in Python
  - can rewrite in something else later

## Permissions

You need to store info about users and permissions somewhere.
This is kind of a circular problem, because you don't want to store them
somewhere a user could modify and escalate their privileges.
I don't want to reserve the "users" collection, because the application
might want to store data in there (like a profile, or settings).
I think I should adopt some naming convention to distinguish "data"
from "metadata": similar to MongoDB's `system.*` collections.
I'll use a `meta.*` prefix, and maybe disallow user collections from
containing a dot.
