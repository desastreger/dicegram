export type DicegramTemplate = {
	id: string;
	name: string;
	description: string;
	source: string;
};

const META_SOURCE = `direction top-to-bottom
setting color_scheme gruvbox

// A meta-Dicegram: the loop we use to build Dicegram itself.

swimlane "User" {
	[circle] spark "Spark" step:0 type:start
	[rounded] ask "Describe\\nthe feature" step:1 type:process owner:"you" status:active
	[diamond] happy "Happy?" step:8 type:decision priority:high
}

swimlane "Claude" {
	box "Think" {fill: rgba(56, 70, 95, 0.25)} {
		[rect] plan "Draft a plan" step:2 type:process
		[rect] scope "Scope & trade-offs" step:3 type:process
	}
	box "Make" {fill: rgba(40, 70, 56, 0.25)} {
		[rect] edit "Edit code" step:4 type:automated status:active
		[hexagon] check "Typecheck + run" step:5 type:automated priority:critical
	}
}

swimlane "Repo" {
	[cylinder] dsl "Canonical DSL" step:6 type:datastore
	[rect] commit "Commit & push" step:7 type:automated
	[circle] ship "Shipped" step:9 type:end
}

spark -> ask
ask -> plan : "prompt"
plan -> scope
scope -> edit
edit ==> check : "verify"
check -> dsl : "writes"
dsl -> commit
commit -> happy : "review"
happy -> ask : "redirect"
happy -> ship : "yes"

note "The DSL is the\\nsource of truth" [dsl]
group "inner loop" { plan scope edit check }
`;

const FLOWCHART_SOURCE = `direction top-to-bottom

[circle] start "Start" step:0 type:start
[rect] step1 "Do the thing" step:1 type:process
[diamond] decide "Looks good?" step:2 type:decision
[rect] step2 "Ship it" step:3 type:process
[circle] end "End" step:4 type:end

start -> step1
step1 -> decide
decide -> step2 : "yes"
decide -> step1 : "no"
step2 -> end
`;

const SDLC_SOURCE = `direction left-to-right
setting color_scheme dracula

swimlane "Product" {
	[circle] idea "Idea" step:0 type:start
	[rounded] scope "Scope" step:1 type:process owner:"pm"
}

swimlane "Engineering" {
	[rect] design "Design" step:2 type:process
	[rect] build "Build" step:3 type:automated status:active
	[hexagon] review "Code review" step:4 type:approval priority:high
	[hexagon] qa "QA" step:5 type:automated
}

swimlane "Release" {
	[cylinder] stage "Staging" step:6 type:datastore
	[circle] live "Live" step:7 type:end
}

idea -> scope
scope -> design
design -> build
build ==> review : "PR"
review -> qa : "approved"
qa --> build : "regressions"
qa -> stage
stage -> live
`;

const EMPTY_SOURCE = `direction top-to-bottom

[rect] start "Start" step:0
`;

export const TEMPLATES: DicegramTemplate[] = [
	{
		id: 'empty',
		name: 'Empty',
		description: 'One rectangle, ready to extend.',
		source: EMPTY_SOURCE
	},
	{
		id: 'flowchart',
		name: 'Simple flowchart',
		description: 'Linear 5-step flow with one decision.',
		source: FLOWCHART_SOURCE
	},
	{
		id: 'sdlc',
		name: 'Software lifecycle',
		description: 'Product → Engineering → Release, left-to-right.',
		source: SDLC_SOURCE
	},
	{
		id: 'meta',
		name: 'Meta-Dicegram',
		description: 'The loop we use to build Dicegram itself.',
		source: META_SOURCE
	}
];

export const DEFAULT_TEMPLATE_ID = 'flowchart';
