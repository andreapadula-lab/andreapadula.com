# Most AI Products Fail — Not Because of the Tech

I've spent the last few years selling AI to banks. Not the TED Talk version of AI. The version that has to survive procurement, compliance reviews, a six-month pilot that nobody internally champions, and a CTO who got burned by the last vendor who promised "intelligent automation."

Here's what I've learned from sitting across the table from C-levels at financial institutions across Europe and the Middle East: the technology almost never kills the deal. What kills it is that nobody checked whether the thing being built was the thing anyone would actually use.

This is not an original observation. A man named Alberto Savoia figured this out years ago — and he did it at Google.

## The Law of Market Failure

Savoia was Google's first Engineering Director. After watching product after product fail despite being built by some of the smartest engineers on the planet, he developed a framework he called pretotyping. He wrote two books about it — *Pretotype It* and *The Right It* — and the core thesis is brutally simple:

Most new products fail in the market. Not because they're badly built. Because they're the wrong product.

He calls it the Law of Market Failure. And it applies whether you're building a consumer app or an AI-powered portfolio optimizer for private banks.

The distinction Savoia draws is between building IT RIGHT and building THE RIGHT IT. Silicon Valley is obsessed with the first. Lean sprints. Clean architecture. Scalable infrastructure. All of that is worthless if the product itself is something nobody needs, wants, or will pay for.

I think about this every single week.

## The AI Strategy Deck Problem

Here's a number I keep coming back to. Roughly 85% of European banks have an AI strategy. About 12% have something meaningful in production. That gap — from 85 to 12 — is not a technology gap. It's not a talent gap. It's not even a budget gap.

It's a validation gap.

What happens is this: a bank hires a consultancy. The consultancy produces a 90-page AI strategy deck. The deck identifies 15 use cases. Each use case gets a "feasibility score" and a "business impact estimate." The board approves three pilots. Twelve months later, two pilots are dead and the third is limping along in a sandbox that four people use.

Nobody pretotyped anything. Nobody tested whether the people who were supposed to benefit from the tool would actually change their behavior. The entire process skipped the most important question — will anyone use this? — and jumped straight to architecture diagrams.

Savoia would recognize this instantly. It's what he calls "thoughtland" — the dangerous territory where ideas sound brilliant because nobody has tested them against reality.

## What They Say vs. What They Do

I talk to bank executives almost every day. I've done it in Milan, Doha, Riyadh, Taipei, Paris, San Francisco. And I've noticed something consistent across every geography and every institution size:

What a C-level says they want in a meeting and what their organization actually adopts are two completely different things.

In meetings, everyone wants AI agents. Autonomous. Proactive. Something that "reasons." Something that impresses the board.

In practice, what gets adopted — what actually survives past the pilot phase — is almost always something simpler. A tool that saves a banker 30 minutes of meeting prep. A compliance check that runs in the background. Something boring. Something that slots into existing workflows without asking anyone to change how they work.

The ambitious stuff dies. Not because it doesn't work technically, but because nobody validated the adoption hypothesis. The team built something impressive. They didn't build something anyone would use.

## Pretotyping Applied to AI

Savoia developed a whole taxonomy of pretotyping techniques. The one I find most relevant to AI is the Mechanical Turk.

The idea is simple: before you build the automation, put a human behind the curtain. Let users interact with what they think is an AI system, but have a human doing the work. Then measure what actually happens. Do people use it? Do they trust the output? Do they change their behavior? Do they come back?

This is incredibly powerful in financial services AI, and almost nobody does it.

Instead, the typical sequence is: raise money, hire ML engineers, spend eight months building a model, realize the training data is a mess, spend four more months cleaning data, ship a beta, discover that the relationship managers won't use it because it doesn't integrate with their CRM, and the compliance team blocks it because nobody consulted them during design.

Imagine if, before writing a single line of model code, someone had put a junior analyst behind a chat interface. The banker types a question about a client's portfolio. The analyst looks it up, formulates a smart answer, and sends it back through the interface. The banker thinks they're talking to an AI.

Now you can test everything that matters. Response time expectations. What questions people actually ask versus what you assumed they'd ask. Whether they trust the output enough to act on it. Whether they use it once out of curiosity or integrate it into their daily routine.

This costs almost nothing. It takes weeks, not months. And it tells you more about product-market fit than any strategy deck ever will.

## The XYZ Hypothesis

Another Savoia concept I think about a lot: the XYZ Hypothesis. Instead of vague statements like "banks want AI for wealth management," you force yourself to be specific. At least X% of Y will Z.

At least 40% of relationship managers at mid-size Italian private banks will use an AI meeting-prep tool at least three times per week within the first month of deployment.

That's testable. That's falsifiable. That's honest.

Most AI companies can't formulate their hypothesis this clearly. They operate in the fog of "AI is the future" and "financial institutions need to modernize." Those aren't hypotheses. Those are vibes.

And vibes don't survive contact with a procurement department.

## Skin in the Game

Savoia insists on "skin in the game" — meaning the people in your test need to invest something real. Time, money, reputation. Not just a survey response. Not just "yeah, I'd use that."

This is where the gap between Europe and Silicon Valley gets interesting. In the Valley, the culture of rapid prototyping and user testing is embedded. It's imperfect, sometimes theatrical, but it's there. In European financial services, the default mode is still top-down. A committee decides what gets built. Users are consulted after the fact, if at all.

I've seen banks spend two years and seven figures building an internal AI tool that their own employees route around because it's slower than the spreadsheet it was supposed to replace. Two years. Nobody asked the people who would use it whether the spreadsheet was actually a problem.

That's not a technology failure. That's an organizational failure to validate.

## What I See From Where I Sit

Working at the intersection of Silicon Valley AI and European banking gives you a specific vantage point. You see the American bias toward building fast and iterating. You see the European bias toward planning thoroughly and building once. Both fail, but they fail differently.

American AI startups fail because they ship something nobody in regulated industries can actually deploy. European initiatives fail because they plan so long that by the time they ship, the market has moved.

The fix for both is the same, and it's Savoia's fix: test the market hypothesis before you invest in the solution. Not with a deck. Not with a survey. With something that forces real behavior from real users with real stakes.

At Streetbeat, this shapes how we think. Not because we read it in a book — though the book is good and you should read it — but because we've made these mistakes ourselves. We've built features that were technically elegant and practically ignored. We've assumed that what a Chief Innovation Officer asks for in a meeting is what their organization will actually adopt. It isn't. You have to test it.

## The Uncomfortable Truth

Here's where I'll be blunt.

Most AI products being built right now for financial services will fail. Not 50%. Not 60%. Most. Savoia's data from other industries suggests failure rates above 80% for new products, and I see no reason why AI in banking would be the exception.

The survivors won't be the ones with the best models. They'll be the ones who figured out, early and cheaply, what the market actually wants — and had the discipline to kill the things it doesn't.

The question is not "can we build an AI that does X?" In 2026, the answer is almost always yes. The question is "will anyone change their behavior because this exists?" And the only way to answer that is to stop building and start testing.

Not testing the technology. Testing the idea.

Alberto Savoia put it better than I can: make sure you are building The Right It before you build It Right.

Most teams in AI get this backwards. The ones who don't are the ones still standing in three years.
