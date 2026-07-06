<script lang="ts">
	import './layout.css';
	import { resolve } from '$app/paths';
	import { onMount } from 'svelte';
	import { getUser, logout, userManager } from '$lib/auth';

	let { children } = $props();

	let userName = $state<string | null>(null);
	let userPicture = $state<string | null>(null);
	let isAdmin = $state(false);

	function applyUser(profile: { name?: string | null; nickname?: string | null; sub?: string; picture?: string | null; groups_direct?: string[] | null }) {
		userName = profile.name ?? profile.nickname ?? profile.sub ?? null;
		userPicture = profile.picture ?? null;
		isAdmin = (profile.groups_direct ?? []).includes('auth/auth-webis-admin');
	}

	onMount(() => {
		getUser()?.then((user) => { if (user && !user.expired) applyUser(user.profile); });

		const onUserLoaded = (u: { profile: Parameters<typeof applyUser>[0] }) => applyUser(u.profile);
		const onUserUnloaded = () => { userName = null; userPicture = null; isAdmin = false; };

		userManager?.events.addUserLoaded(onUserLoaded);
		userManager?.events.addUserUnloaded(onUserUnloaded);
		return () => {
			userManager?.events.removeUserLoaded(onUserLoaded);
			userManager?.events.removeUserUnloaded(onUserUnloaded);
		};
	});
</script>

<svelte:head>
    <!--<link rel="stylesheet" href="https://assets.webis.de/css/style.css">-->
</svelte:head>

<div class="min-h-screen flex flex-col">

<nav
	class="w-full shadow-sm mb-3 md:mb-4 xl:mb-5"
	style="background: linear-gradient(to bottom, #f8f9fa, #e9ecef)"
>
	<div class="w-full px-4 h-[70px] flex items-center justify-between">
		<div class="flex items-center gap-4">
			<a
				class="flex items-center h-10 text-xl font-normal text-black/90 no-underline"
				href={resolve('/')}
			>
				<span><span style="color:#951515"><b>IR</b></span> Anthology</span>
			</a>
			<a href={resolve('/anthology')} class="text-sm text-gray-600 no-underline border border-gray-300 rounded px-3 py-1 hover:bg-gray-200 transition-colors">Browse by Venue</a>
		</div>
		{#if userName}
			<div class="relative group">
				<button class="flex items-center gap-2 text-black/80 hover:text-black bg-transparent border-none cursor-pointer">
					{#if isAdmin}
						<span class="text-xs font-medium bg-red-100 text-red-700 border border-red-200 rounded px-2 py-0.5">Admin</span>
					{/if}
					{#if userPicture}
						<img src={userPicture} alt="avatar" class="w-8 h-8 rounded-full border border-gray-300">
					{/if}
					<span class="text-sm font-medium">{userName}</span>
				</button>
				<div class="absolute right-0 top-full w-40 bg-white rounded shadow-lg border border-gray-100 z-50
				opacity-0 invisible [transition:opacity_0s_100ms,visibility_0s_100ms]
				group-hover:opacity-100 group-hover:visible group-hover:[transition:opacity_0s,visibility_0s]
				before:absolute before:inset-x-0 before:-top-2 before:h-2 before:content-['']">
					<a href={resolve('/admin')} class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 no-underline">Admin</a>
					<button onclick={logout} class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 border-none bg-transparent cursor-pointer">Log out</button>
				</div>
			</div>
		{/if}
	</div>

</nav>

<main class="flex-1 px-6 md:px-10">
	{@render children()}
</main>

<footer
	class="mt-3 md:mt-6 xl:mt-12 py-4"
	style="background: linear-gradient(180deg, #f3f4f6 0%, #e5e7eb 100%)"
>
	<div class="w-full px-4">
		<p class="text-sm text-gray-500 m-0 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 sm:px-3">
			<span class="inline-flex items-center flex-wrap gap-1">
				<a style="color:#6c757d" href="/anthology/info/credits/">Credits</a>
				<span class="mx-1">•</span>
				<a
					style="color:#6c757d"
					href="https://github.com/ir-anthology/ir-anthology/blob/master/CONTRIBUTE.md"
					>
					Contribute
				</a>
			</span>
			<span class="inline-flex items-center flex-wrap gap-1 justify-end">
				©2023
				<a style="color:#6c757d" href="https://webis.de/">Webis Group</a>
				<span class="mx-1">•</span>
				<a href="https://github.com/ir-anthology/ir-anthology" aria-label="GitHub repository">
					<svg width="16" height="16" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
						<path
							d="M10 1C5.03 1 1 5.03 1 10c0 3.98 2.58 7.35 6.16 8.54C7.61 18.62 7.77 18.34 7.77 18.11 7.77 17.9 7.76 17.33 7.76 16.58 5.26 17.12 4.73 15.37 4.73 15.37c-.41-1.04-1-1.32-1-1.32C2.91 13.5 3.79 13.5 3.79 13.5 4.69 13.56 5.17 14.43 5.17 14.43c.8 1.37 2.11.98 2.62.75C7.87 14.6 8.1 14.2 8.36 13.98c-2-.23-4.1-1-4.1-4.45C4.26 8.55 4.61 7.74 5.19 7.11 5.1 6.88 4.79 5.97 5.28 4.73c0 0 .76-.24 2.47.92C8.47 5.45 9.24 5.35 10 5.35S11.53 5.45 12.25 5.65c1.72-1.17 2.47-.92 2.47-.92C15.21 5.97 14.9 6.88 14.81 7.11c.58.63.92 1.43.92 2.42.0 3.46-2.1 4.22-4.11 4.44C11.94 14.25 12.23 14.8 12.23 15.64 12.23 16.84 12.22 17.81 12.22 18.11 12.22 18.35 12.38 18.63 12.84 18.54 16.42 17.35 19 13.98 19 10c0-4.97-4.03-9-9-9z"
							fill="#6c757d"
						></path>
					</svg>
				</a>
				<a href="https://twitter.com/IRanthology" aria-label="Twitter">
					<svg width="18" height="18" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
						<path
							d="M19 4.74C18.339 5.029 17.626 5.229 16.881 5.32 17.644 4.86 18.227 4.139 18.503 3.28 17.79 3.7 17.001 4.009 16.159 4.17 15.485 3.45 14.526 3 13.464 3 11.423 3 9.771 4.66 9.771 6.7 9.771 6.99 9.804 7.269 9.868 7.539c-3.073-.159-5.792-1.62-7.614-3.86C1.936 4.219 1.754 4.86 1.754 5.539c0 1.281.651 2.411 1.643 3.071C2.79 8.589 2.22 8.429 1.723 8.149V8.189c0 1.789 1.274 3.289 2.963 3.631C4.376 11.899 4.049 11.939 3.713 11.939 3.475 11.939 3.245 11.919 3.018 11.88c.472 1.469 1.834 2.539 3.451 2.569-1.264.98-2.857 1.57-4.587 1.57C1.583 16.019 1.29 16.009 1 15.969c1.635 1.05 3.576 1.66 5.662 1.66 6.792.0 10.508-5.629 10.508-10.5C17.17 6.969 17.166 6.809 17.157 6.649 17.879 6.129 18.504 5.478 19 4.74"
							fill="#6c757d"
						></path>
					</svg>
				</a>
				<span class="mx-1">•</span>
				<a style="color:#6c757d" href="https://webis.de/people.html">Contact</a>
				<span class="mx-1">•</span>
				<a style="color:#6c757d" href="https://webis.de/legal.html">Impressum / Terms / Privacy</a>
			</span>
		</p>
	</div>
</footer>

</div>