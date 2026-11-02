<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { resolve } from '$app/paths';
    import { userManager } from '$lib/auth';

    onMount(async () => {
        await userManager?.signinRedirectCallback();
        goto(resolve('/admin'));
    });
</script>