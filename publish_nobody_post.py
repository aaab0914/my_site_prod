
from django.utils import timezone
from django.contrib.auth import get_user_model
from blog.models import Post

User = get_user_model()
author, created = User.objects.get_or_create(username='Ron_prod')

if created:
    author.set_password('your_secure_password_here')
    author.save()
    print("User 'Ron_prod' created successfully.")
else:
    print("User 'Ron_prod' found.")

slug = 'there-is-nobody-here-anymore-the-silence-of-virtual-places'
existing = Post.objects.filter(slug=slug).first()
if existing:
    post = existing
    post.title = 'There is nobody here anymore'
    post.author = author
    post.body = """
# There is nobody here anymore

I logged in tonight just to check. Out of habit, really. The cursor blinked patiently in the password field, and I typed my credentials without thinking. The screen loaded, and then I saw it: the empty dashboard, the silent chat log, the last message sent three years ago.

There is nobody here anymore.

It’s a strange feeling, standing in the middle of a digital place that used to be crowded. Like walking into your childhood schoolyard after the bell has rung, and everyone has gone home. The swings are still there. The basketball hoops are still there. But the air is different. It is still. It carries no noise.

## The ghosts in the machine

Back then, this place was alive. Notifications popped up like fireflies in summer. Avatars shifted in and out of conversations. There were inside jokes, arguments that lasted until 3 a.m., shared links that opened new universes. We were all so sure that the world we built here would last forever.

But forever is a fragile thing. People grow up, change jobs, move cities. They forget passwords. They get tired of the noise and migrate to newer, shinier platforms. One by one, the green status dots turned gray, and then they simply disappeared. No farewells. No dramatic goodbyes. Just a gradual fading.

## The illusion of permanence

We spend so much time curating our digital footprints. We post, we comment, we share. We believe that these pixels and bits are extensions of ourselves, that they will persist as monuments to who we were. But the server rooms where we live are leased, and the cloud is just someone else’s hard drive. When the bills stop getting paid, the power goes out, and the data evaporates into nothing.

The internet has no memory of its own. It only remembers what we feed it. And when we stop feeding it, it goes quiet. It is the most honest mirror of human attention: it only exists as long as we are looking.

## The silence of the login screen

Tonight, I scrolled through the remnants of that old world. I saw a draft of a post I never published. I saw a private message from someone I no longer know, asking if I had ever finished reading that book they recommended. I opened the folder of shared photos and saw faces I haven't seen in years, frozen in a specific afternoon, laughing about something that now makes no sense to me.

It’s not sad, exactly. It’s hollow. It feels like opening a drawer in a hotel room that someone else left behind. The traces are there, but the person is gone. And the realization settles in: the person you were, the person who typed those messages and laughed at those jokes, is gone too.

## A new kind of loneliness

We have invented a new kind of loneliness in this century. It is not the solitude of the wilderness. It is the solitude of a crowded room where every voice is recorded but none is present. We are surrounded by the artifacts of connection, but the connection itself has dissolved.

There is nobody here anymore. But the page still loads. The script still runs. The database still holds the rows of my old self. And I find myself wondering: if I reply to that three-year-old message, will anyone be on the other side? Or will I simply be speaking into the void, comforting myself with the echo of my own voice?

## Conclusion

Maybe this is what we leave behind. Not grand legacies or monuments, but a trail of small, forgotten interactions—a comment on a friend’s birthday post, a reply in a forgotten forum, a shared link that changed nothing.

We came here thinking it was infinite. But the only thing that really endures is the quiet, patient cursor, still blinking in the dark, waiting for someone to type again.

There is nobody here anymore. And yet, somehow, I am still here. Watching. Remembering. Typing a message that will never be delivered.

The silence is the only reply.
"""
    post.publish = timezone.now()
    post.status = Post.Status.PUBLISHED
    post.save()
    print(f"Existing post '{post.title}' updated and published.")
else:
    post = Post(
        title='There is nobody here anymore',
        slug=slug,
        author=author,
        body="""
# There is nobody here anymore

I logged in tonight just to check. Out of habit, really. The cursor blinked patiently in the password field, and I typed my credentials without thinking. The screen loaded, and then I saw it: the empty dashboard, the silent chat log, the last message sent three years ago.

There is nobody here anymore.

It’s a strange feeling, standing in the middle of a digital place that used to be crowded. Like walking into your childhood schoolyard after the bell has rung, and everyone has gone home. The swings are still there. The basketball hoops are still there. But the air is different. It is still. It carries no noise.

## The ghosts in the machine

Back then, this place was alive. Notifications popped up like fireflies in summer. Avatars shifted in and out of conversations. There were inside jokes, arguments that lasted until 3 a.m., shared links that opened new universes. We were all so sure that the world we built here would last forever.

But forever is a fragile thing. People grow up, change jobs, move cities. They forget passwords. They get tired of the noise and migrate to newer, shinier platforms. One by one, the green status dots turned gray, and then they simply disappeared. No farewells. No dramatic goodbyes. Just a gradual fading.

## The illusion of permanence

We spend so much time curating our digital footprints. We post, we comment, we share. We believe that these pixels and bits are extensions of ourselves, that they will persist as monuments to who we were. But the server rooms where we live are leased, and the cloud is just someone else’s hard drive. When the bills stop getting paid, the power goes out, and the data evaporates into nothing.

The internet has no memory of its own. It only remembers what we feed it. And when we stop feeding it, it goes quiet. It is the most honest mirror of human attention: it only exists as long as we are looking.

## The silence of the login screen

Tonight, I scrolled through the remnants of that old world. I saw a draft of a post I never published. I saw a private message from someone I no longer know, asking if I had ever finished reading that book they recommended. I opened the folder of shared photos and saw faces I haven't seen in years, frozen in a specific afternoon, laughing about something that now makes no sense to me.

It’s not sad, exactly. It’s hollow. It feels like opening a drawer in a hotel room that someone else left behind. The traces are there, but the person is gone. And the realization settles in: the person you were, the person who typed those messages and laughed at those jokes, is gone too.

## A new kind of loneliness

We have invented a new kind of loneliness in this century. It is not the solitude of the wilderness. It is the solitude of a crowded room where every voice is recorded but none is present. We are surrounded by the artifacts of connection, but the connection itself has dissolved.

There is nobody here anymore. But the page still loads. The script still runs. The database still holds the rows of my old self. And I find myself wondering: if I reply to that three-year-old message, will anyone be on the other side? Or will I simply be speaking into the void, comforting myself with the echo of my own voice?

## Conclusion

Maybe this is what we leave behind. Not grand legacies or monuments, but a trail of small, forgotten interactions—a comment on a friend’s birthday post, a reply in a forgotten forum, a shared link that changed nothing.

We came here thinking it was infinite. But the only thing that really endures is the quiet, patient cursor, still blinking in the dark, waiting for someone to type again.

There is nobody here anymore. And yet, somehow, I am still here. Watching. Remembering. Typing a message that will never be delivered.

The silence is the only reply.
""",
        publish=timezone.now(),
        status=Post.Status.PUBLISHED,
    )
    post.save()
    print(f"Post '{post.title}' has been published successfully!")

post.tags.set(['#life', '#philosophy', '#digital', '#silence', '#nostalgia'])
post.save()
print('id=', post.id)
print('url=', post.get_absolute_url())
print('tags=', ','.join(post.tags.names()))
