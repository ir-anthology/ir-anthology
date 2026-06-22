<script lang="ts">
    import { login } from '$lib/auth';
    import { base } from '$app/paths';
</script>

<div class="flex items-center justify-center min-h-[60vh]">
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm px-10 py-12 w-full max-w-sm text-center">

        <a href="{base}/" class="inline-block mb-8 text-2xl font-normal text-black/90 no-underline">
            <span style="color:#951515"><b>IR</b></span> Anthology
        </a>

        <p class="text-gray-500 text-sm mb-8">Sign in to access restricted content.</p>

        <button
            onclick={login}
            class="inline-flex items-center gap-3 w-full justify-center px-4 py-2.5 rounded border border-gray-300 bg-white hover:bg-gray-50 text-sm font-medium text-gray-700 transition-colors"
        >
            <!-- GitLab tanuki logo -->
            <svg width="20" height="20" viewBox="0 0 380 380" xmlns="http://www.w3.org/2000/svg">
                <path d="M282.83 170.73l-.27-.69-26.14-68.22a6.81 6.81 0 00-2.69-3.24 7 7 0 00-8 .43 7 7 0 00-2.32 3.52l-17.65 54H154.29l-17.65-54a6.86 6.86 0 00-2.32-3.52 7 7 0 00-8-.43 6.85 6.85 0 00-2.69 3.24L97.44 170l-.26.69a48.54 48.54 0 0016.1 56.1l.09.07.24.17 39.82 29.82 19.7 14.91 12 9.06a8.07 8.07 0 009.19 0l12-9.06 19.7-14.91 40.06-30 .1-.08a48.56 48.56 0 0016.07-56.04z" fill="#E24329"/>
                <path d="M282.83 170.73l-.27-.69a88.3 88.3 0 00-35.15 15.8L190 229.25c19.55 14.79 36.57 27.64 36.57 27.64l40.06-30 .1-.08a48.56 48.56 0 0016.1-56.08z" fill="#FC6D26"/>
                <path d="M153.43 256.89l19.7 14.91 12 9.06a8.07 8.07 0 009.19 0l12-9.06 19.7-14.91S189.55 244 190 229.25c-.45 14.75-36.57 27.64-36.57 27.64z" fill="#FCA326"/>
                <path d="M132.58 185.84A88.19 88.19 0 0097.44 170l-.26.69a48.54 48.54 0 0016.1 56.1l.09.07.24.17 39.82 29.82s17-12.85 36.57-27.64z" fill="#FC6D26"/>
            </svg>
            Sign in with GitLab
        </button>

    </div>
</div>
